from .core.config import settings, SessionLocal
from .core.analysis import run_wallet_analysis
from .core.models import AnalysisJob, WalletAnalysis
from .core import settings_service, sanctions_service
from celery import Celery
from celery.schedules import crontab
import logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery(
    'tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # M6: Store beat schedule in Redis instead of local file
    beat_schedule_filename=None,
    # Reliability: ack tasks only after completion so restarts don't lose work
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Prefetch 1 task per greenlet — prevents the worker from pulling all 100K tasks
    # into memory at once, which causes task loss on restart
    worker_prefetch_multiplier=1,
    # L5: Task rate limiting (1000/m per worker)
    task_annotations={
        'tasks.analyze_wallet': {'rate_limit': '1000/m'},
    },
)

# Periodic task schedule (requires celery beat)
celery_app.conf.beat_schedule = {
    "update-sanctions-lists": {
        "task": "tasks.update_sanctions",
        # timedelta: fires immediately on first start (never-run), then every 24h
        "schedule": timedelta(hours=24),
    },
    # C2: Reap stale jobs stuck in IN_PROGRESS for more than 30 minutes
    "reap-stale-jobs": {
        "task": "tasks.reap_stale_jobs",
        "schedule": crontab(minute="*/10"),  # Check every 10 minutes
    },
}

@celery_app.task(name='tasks.process_wallet_list')
def process_wallet_list(job_id: int, wallets: list[dict]):
    """
    Celery task to dispatch analysis tasks for a chunk of wallets.
    Checks job status first — skips dispatch if job was paused or stopped.
    """
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job and job.status in ('STOPPED', 'PAUSED'):
            logger.info(f"Job {job_id} is {job.status}, skipping dispatch of {len(wallets)} wallets")
            return
    finally:
        db.close()

    logger.info(f"Dispatching {len(wallets)} wallet tasks for job {job_id}")
    for wallet_info in wallets:
        analyze_wallet.delay(job_id, wallet_info['address'], wallet_info['chain'])

@celery_app.task(
    name='tasks.analyze_wallet',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 5},
    # C2: Per-wallet task timeouts
    soft_time_limit=120,
    time_limit=150,
)
def analyze_wallet(job_id: int, address: str, chain: str):
    """
    Celery task to perform the two-pass analysis for a single wallet.
    DB connection is held only for quick reads/writes — released during the long HTTP analysis
    so gevent workers don't exhaust the connection pool.
    """
    logger.info(f"Analyzing wallet {address} on {chain} for job {job_id}")

    # Phase 1: quick DB reads — fetch settings, then release connection
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job and job.status in ('STOPPED', 'PAUSED'):
            logger.info(f"Job {job_id} is {job.status}, skipping analysis for {address}")
            return
        project_name = job.project_name if job else None
        effective_settings = settings_service.get_effective_settings(project_name=project_name, db=db)
    finally:
        db.close()

    # Phase 2: long HTTP analysis — no DB connection held
    analysis_data = None
    error_msg = None
    try:
        analysis_data = run_wallet_analysis(address, chain, effective_settings=effective_settings)
    except Exception as e:
        logger.error(f"Failed to analyze wallet {address} on {chain}: {e}", exc_info=True)
        error_msg = str(e)

    # Phase 3: quick DB write — save result or failure record
    db = SessionLocal()
    try:
        # Re-check status: job may have been stopped/paused while Phase 2 was running
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job and job.status in ('STOPPED', 'PAUSED'):
            logger.info(f"Job {job_id} is {job.status}, discarding result for {address}")
            return

        if analysis_data is not None:
            wallet_record = WalletAnalysis(job_id=job_id, **analysis_data)
            db.add(wallet_record)
            db.commit()
            logger.info(f"Successfully analyzed and saved wallet {address} on {chain}")
        else:
            failed_record = WalletAnalysis(
                job_id=job_id,
                address=address,
                chain=chain,
                tier='UNKNOWN',
                notes=f"Analysis failed: {error_msg}"
            )
            db.add(failed_record)
            db.commit()
    except Exception as e:
        logger.error(f"Failed to save result for wallet {address}: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


@celery_app.task(name='tasks.update_sanctions')
def update_sanctions_task():
    """Periodic task to refresh all enabled sanctions lists.
    Delegates to the API endpoint via local HTTP to avoid gevent SSL issues
    with large file downloads (OFAC XML is ~100MB).
    """
    logger.info("Starting periodic sanctions list update")
    import requests as _req
    try:
        resp = _req.post(
            "http://api:8000/admin/sanctions/update",
            headers={"X-API-Key": settings.ADMIN_API_KEY},
            timeout=900,  # allow up to 15 min for OFAC XML download + parse
        )
        resp.raise_for_status()
        result = resp.json()
        logger.info(f"Sanctions update completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to update sanctions lists: {e}", exc_info=True)
        raise


@celery_app.task(name='tasks.reap_stale_jobs')
def reap_stale_jobs():
    """
    C2: Periodic task to find jobs stuck in IN_PROGRESS for too long and mark them FAILED.
    This prevents jobs from staying in a zombie state forever.
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        # Find all long-running IN_PROGRESS jobs (started > 10 minutes ago)
        early_cutoff = now - timedelta(minutes=10)
        stale_jobs = (
            db.query(AnalysisJob)
            .filter(
                AnalysisJob.status == 'IN_PROGRESS',
                AnalysisJob.started_at < early_cutoff,
            )
            .all()
        )

        for job in stale_jobs:
            processed = db.query(WalletAnalysis).filter(WalletAnalysis.job_id == job.id).count()

            # If all wallets processed, mark as completed
            if processed >= job.total_wallets:
                job.status = 'COMPLETED'
                job.completed_at = now
                if job.started_at:
                    job.analysis_duration_seconds = (job.completed_at - job.started_at).total_seconds()
                logger.info(f"Reaper: completed job {job.id} ({processed}/{job.total_wallets} wallets)")
            else:
                # Allow more time based on job size: ~4s per wallet, min 60min, max 5 days
                # 500K wallets observed at ~277/min (30h) — give generous 2× buffer
                allowed_minutes = max(60, min(7200, job.total_wallets // 15))
                timeout_cutoff = now - timedelta(minutes=allowed_minutes)
                if job.started_at and job.started_at.replace(tzinfo=timezone.utc) < timeout_cutoff:
                    job.status = 'FAILED'
                    job.result = f"Timed out after {allowed_minutes} minutes ({processed}/{job.total_wallets} wallets processed)"
                    job.completed_at = now
                    if job.started_at:
                        job.analysis_duration_seconds = (job.completed_at - job.started_at).total_seconds()
                    logger.warning(f"Reaper: failed job {job.id} ({processed}/{job.total_wallets} wallets, timeout={allowed_minutes}m)")

        if stale_jobs:
            db.commit()
            logger.info(f"Reaper: processed {len(stale_jobs)} stale jobs")

    except Exception as e:
        logger.error(f"Error in reap_stale_jobs: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
