from .core.config import settings, SessionLocal
from .core.analysis import run_wallet_analysis
from .core.models import AnalysisJob, WalletAnalysis
from .core import settings_service, sanctions_service
from celery import Celery
from celery.schedules import crontab
import logging

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
)

# Periodic task schedule (requires celery beat)
celery_app.conf.beat_schedule = {
    "update-sanctions-lists": {
        "task": "tasks.update_sanctions",
        "schedule": crontab(hour="*/24"),
    },
}

@celery_app.task(name='tasks.process_wallet_list')
def process_wallet_list(job_id: int, wallets: list[dict]):
    """
    Celery task to process a list of wallets for a given job.
    It spawns individual tasks for each wallet.
    """
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            logger.error(f"Job with ID {job_id} not found.")
            return

        job.status = 'IN_PROGRESS'
        db.commit()

        for wallet_info in wallets:
            analyze_wallet.delay(job_id, wallet_info['address'], wallet_info['chain'])

    except Exception as e:
        logger.error(f"Error in process_wallet_list for job {job_id}: {e}")
        job.status = 'FAILED'
        job.result = str(e)
        db.commit()
    finally:
        db.close()

@celery_app.task(
    name='tasks.analyze_wallet',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60}
)
def analyze_wallet(job_id: int, address: str, chain: str):
    """
    Celery task to perform the two-pass analysis for a single wallet.
    Fetches effective settings for the job's project and passes them to analysis.
    """
    logger.info(f"Analyzing wallet {address} on {chain} for job {job_id}")
    db = SessionLocal()
    try:
        # Look up project_name for this job to fetch project-specific settings
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        project_name = job.project_name if job else None

        # Get effective settings (global + project overrides)
        effective_settings = settings_service.get_effective_settings(project_name=project_name, db=db)

        # Run the core analysis logic with settings
        analysis_data = run_wallet_analysis(address, chain, effective_settings=effective_settings)

        # Save the result to the database
        wallet_record = WalletAnalysis(job_id=job_id, **analysis_data)
        db.add(wallet_record)
        db.commit()
        logger.info(f"Successfully analyzed and saved wallet {address} on {chain}")

    except Exception as e:
        logger.error(f"Failed to analyze wallet {address} on {chain}: {e}", exc_info=True)
        # Optionally, save a failure record
        failed_record = WalletAnalysis(
            job_id=job_id,
            address=address,
            chain=chain,
            tier='UNKNOWN',
            notes=f"Analysis failed: {str(e)}"
        )
        db.add(failed_record)
        db.commit()
    finally:
        db.close()


@celery_app.task(name='tasks.update_sanctions')
def update_sanctions_task():
    """Periodic task to refresh all enabled sanctions lists."""
    logger.info("Starting periodic sanctions list update")
    db = SessionLocal()
    try:
        effective_settings = settings_service.get_effective_settings(db=db)
        results = sanctions_service.update_all_lists(db=db, settings=effective_settings)
        logger.info(f"Sanctions update results: {results}")
        return results
    except Exception as e:
        logger.error(f"Failed to update sanctions lists: {e}", exc_info=True)
        raise
    finally:
        db.close()
