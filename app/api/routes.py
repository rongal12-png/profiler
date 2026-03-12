import re

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
import pandas as pd
import io
import json
from typing import Literal
from datetime import datetime, timezone
import markdown2

from ..core import models, reporting, project_health
from ..core.reporting import jinja_env, generate_pdf
from ..worker import process_wallet_list
from ..core.config import get_db

router = APIRouter()

# EVM address pattern (0x + 40 hex chars)
_EVM_ADDRESS_RE = re.compile(r'^0x[0-9a-fA-F]{40}$')
# Solana address pattern (base58, 32-44 chars)
_SOLANA_ADDRESS_RE = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')

SUPPORTED_CHAINS = {"ethereum", "base", "arbitrum", "polygon", "optimism", "bsc", "avalanche", "fantom", "solana"}

# "evm" expands to these 5 chains automatically
EVM_MULTI_CHAINS = ["ethereum", "base", "arbitrum", "bsc", "polygon"]


def _parse_chain_list(chain_str: str) -> list[str]:
    """
    Parse chain column value into a list of individual chains.
    Supports: single chain, "evm" shortcut, or comma-separated combinations.
    Examples:
      "ethereum"         → ["ethereum"]
      "evm"              → ["ethereum","base","arbitrum","bsc","polygon"]
      "ethereum,base"    → ["ethereum","base"]
      "base,ethereum,bsc"→ ["base","ethereum","bsc"]
    """
    s = chain_str.strip().lower()
    if s == "evm":
        return EVM_MULTI_CHAINS
    if "," in s:
        return [c.strip() for c in s.split(",") if c.strip()]
    return [s]


def _validate_wallet_address(address: str, chain: str) -> str | None:
    """Validate wallet address format for a single resolved chain. Returns error or None."""
    if chain not in SUPPORTED_CHAINS:
        return f"Unsupported chain: {chain}"
    if chain == "solana":
        if not _SOLANA_ADDRESS_RE.match(address):
            return f"Invalid Solana address: {address}"
    else:
        if not _EVM_ADDRESS_RE.match(address):
            return f"Invalid EVM address: {address}"
    return None


@router.get("/jobs", tags=["Jobs"])
def list_jobs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Returns a list of all analysis jobs, most recent first."""
    jobs = (
        db.query(models.AnalysisJob)
        .order_by(models.AnalysisJob.created_at.desc())
        .limit(limit)
        .all()
    )
    result = []
    for job in jobs:
        processed = db.query(models.WalletAnalysis).filter(models.WalletAnalysis.job_id == job.id).count()
        result.append({
            "job_id": job.id,
            "status": job.status.value if hasattr(job.status, 'value') else job.status,
            "project_name": job.project_name,
            "total_wallets": job.total_wallets,
            "wallets_processed": processed,
            "created_at": str(job.created_at) if job.created_at else None,
        })
    return result


@router.post("/jobs/submit", tags=["Jobs"])
def submit_job(
    file: UploadFile = File(...),
    project_name: str = Form("Project"),
    db: Session = Depends(get_db),
):
    """
    Accepts a CSV file of wallets to start a new analysis job.
    The CSV must have 'address' and 'chain' columns.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    try:
        contents = file.file.read()
        df = pd.read_csv(io.BytesIO(contents))

        if not {'address', 'chain'}.issubset(df.columns):
            raise HTTPException(status_code=400, detail="CSV must contain 'address' and 'chain' columns.")

        # Strip whitespace and normalize
        df['address'] = df['address'].astype(str).str.strip()
        df['chain'] = df['chain'].astype(str).str.strip().str.lower()

        # Expand multi-chain values ("evm", "ethereum,base", etc.) into individual rows
        expanded_rows = []
        for _, row in df.iterrows():
            for chain in _parse_chain_list(row['chain']):
                expanded_rows.append({'address': row['address'], 'chain': chain})
        df = pd.DataFrame(expanded_rows)

        # Validate addresses against resolved chains (H1)
        invalid = []
        for _, row in df.iterrows():
            err = _validate_wallet_address(row['address'], row['chain'])
            if err:
                invalid.append(err)
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid addresses found: {'; '.join(invalid[:5])}"
                + (f" ... and {len(invalid) - 5} more" if len(invalid) > 5 else "")
            )

        # Deduplicate by (address, chain) - C1: prevent duplicate work
        df = df.drop_duplicates(subset=['address', 'chain'])
        wallets = df[['address', 'chain']].to_dict('records')

        if len(wallets) == 0:
            raise HTTPException(status_code=400, detail="No valid wallets found in CSV.")

        # Enforce max wallets per job
        max_wallets = 1_000_000
        if len(wallets) > max_wallets:
            raise HTTPException(status_code=400, detail=f"Too many wallets. Maximum is {max_wallets:,}.")

        new_job = models.AnalysisJob(
            total_wallets=len(wallets),
            project_name=project_name.strip() or "Project",
            status='IN_PROGRESS',
            started_at=datetime.now(timezone.utc),
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        # Dispatch in chunks of 10K so no single task payload exceeds ~500KB
        # and no dispatch task runs longer than a few seconds.
        chunk_size = 10_000
        for i in range(0, len(wallets), chunk_size):
            process_wallet_list.delay(new_job.id, wallets[i:i + chunk_size])

        return JSONResponse(
            status_code=200,
            content={"message": "Job submitted successfully", "job_id": new_job.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@router.get("/jobs/{job_id}/status", tags=["Jobs"])
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Retrieves the current status of an analysis job."""
    job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    processed_count = db.query(models.WalletAnalysis).filter(models.WalletAnalysis.job_id == job_id).count()

    if job.status == 'IN_PROGRESS' and processed_count >= job.total_wallets:
        job.status = 'COMPLETED'
        job.completed_at = datetime.now(timezone.utc)

        # Calculate duration if we have started_at
        if job.started_at and job.completed_at:
            job.analysis_duration_seconds = (job.completed_at - job.started_at).total_seconds()

        db.commit()
        db.refresh(job)

    # Calculate elapsed time for in-progress jobs
    elapsed_seconds = None
    if job.started_at:
        if job.completed_at:
            elapsed_seconds = job.analysis_duration_seconds
        else:
            # Still running - calculate current elapsed time
            elapsed_seconds = (datetime.now(timezone.utc) - job.started_at).total_seconds()

    return {
        "job_id": job.id,
        "status": job.status,
        "total_wallets": job.total_wallets,
        "wallets_processed": processed_count,
        "project_name": job.project_name,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "elapsed_seconds": elapsed_seconds,
        "result": job.result,
    }


@router.get("/jobs/{job_id}/report", tags=["Reports"])
def get_job_report(
    job_id: int,
    format: Literal['json', 'csv', 'markdown', 'html', 'pdf', 'docx'] = Query('json', description="Report format."),
    db: Session = Depends(get_db),
):
    """Generates and returns the report for a completed job."""
    job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != 'COMPLETED':
        raise HTTPException(status_code=400, detail=f"Job is not complete. Current status: {job.status}")

    results = db.query(models.WalletAnalysis).filter(models.WalletAnalysis.job_id == job_id).all()
    if not results:
        raise HTTPException(status_code=404, detail="No analysis results found for this job.")

    project_name = job.project_name or "Project"
    df = reporting.results_to_dataframe(results)

    if format == 'json':
        import math as _math, logging as _logging
        _log = _logging.getLogger(__name__)
        try:
            community_score = project_health.compute_community_quality_score(df)
            health_flags = project_health.compute_health_flags(df)
            concentration_metrics = project_health.compute_concentration_metrics(df)
            token_intel_agg = reporting._aggregate_token_intelligence(df)
            intent_agg = reporting._aggregate_intent_signals(df)

            response_data = {
                "project_name": project_name,
                "job_id": job_id,
                "reference_id": reporting.generate_reference_id(job_id),
                "total_wallets": len(df),
                "wallets": json.loads(df.to_json(orient='records')),
                "aggregates": {
                    "community_score": community_score,
                    "health_flags": health_flags,
                    "concentration_metrics": concentration_metrics,
                    "token_intelligence": token_intel_agg,
                    "intent_signals": intent_agg,
                    "tier_distribution": df['tier'].value_counts().to_dict() if 'tier' in df.columns else {},
                    "persona_distribution": df['persona'].value_counts().to_dict() if 'persona' in df.columns else {},
                    "chain_distribution": df['chain'].value_counts().to_dict() if 'chain' in df.columns else {},
                    "wallet_type_distribution": df['wallet_type'].value_counts().to_dict() if 'wallet_type' in df.columns else {},
                },
            }

            def _json_default(obj):
                if isinstance(obj, float) and (_math.isnan(obj) or _math.isinf(obj)):
                    return None
                return str(obj)
            return Response(content=json.dumps(response_data, default=_json_default), media_type='application/json')
        except Exception as e:
            _log.exception(f"JSON report generation failed for job {job_id}")
            raise HTTPException(status_code=500, detail=f"Report generation error: {type(e).__name__}: {e}")
    elif format == 'csv':
        csv_content = df.to_csv(index=False)
        return Response(
            content=csv_content,
            media_type='text/csv',
            headers={"Content-Disposition": f'attachment; filename="{project_name}-report-{job_id}.csv"'},
        )
    elif format == 'markdown':
        md_content = reporting.generate_executive_report(df, job_id, project_name=project_name)
        return Response(content=md_content, media_type='text/markdown')
    elif format == 'html':
        html_content = reporting.generate_executive_report(df, job_id, project_name=project_name, output_format='html')
        return Response(content=html_content, media_type='text/html')
    elif format == 'pdf':
        html_content = reporting.generate_executive_report(df, job_id, project_name=project_name, output_format='html')
        pdf_bytes = reporting.generate_pdf(html_content)
        safe_name = project_name.replace('"', '').replace(' ', '_')
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={"Content-Disposition": f'attachment; filename="{safe_name}-report-{job_id}.pdf"'},
        )
    elif format == 'docx':
        html_content = reporting.generate_executive_report(df, job_id, project_name=project_name, output_format='html')
        docx_bytes = reporting.generate_docx(html_content, project_name)
        safe_name = project_name.replace('"', '').replace(' ', '_')
        return Response(
            content=docx_bytes,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={"Content-Disposition": f'attachment; filename="{safe_name}-report-{job_id}.docx"'},
        )


@router.post("/jobs/{job_id}/report/custom-pdf", tags=["Reports"])
async def generate_custom_pdf(
    job_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Accepts edited markdown content (text/plain body) and returns a PDF.
    Allows users to download a PDF of their manually-edited report.
    """
    job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == job_id).first()
    project_name = job.project_name if job else "Project"

    md_content = (await request.body()).decode("utf-8")
    html_body = markdown2.markdown(md_content, extras=["tables", "fenced-code-blocks"])
    html_content = reporting._wrap_html(html_body, project_name)
    pdf_bytes = reporting.generate_pdf(html_content)

    safe_name = project_name.replace('"', '').replace(' ', '_')
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}-edited-{job_id}.pdf"'},
    )


@router.get("/guide/pdf", tags=["Guide"])
def download_guide_pdf(lang: str = Query("he", regex="^(he|en)$")):
    """Generate and download the system guide as a PDF."""
    template = jinja_env.get_template("guide_template.html")
    html = template.render(lang=lang, current_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    pdf_bytes = generate_pdf(html)
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={"Content-Disposition": f'attachment; filename="wallet-intelligence-guide-{lang}.pdf"'},
    )
