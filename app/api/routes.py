from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
import pandas as pd
import io
import json
from typing import Literal
from datetime import datetime, timezone

from ..core import models, reporting, project_health
from ..worker import process_wallet_list
from ..core.config import get_db

router = APIRouter()


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

        wallets = df[['address', 'chain']].to_dict('records')

        new_job = models.AnalysisJob(
            total_wallets=len(wallets),
            project_name=project_name.strip() or "Project",
            status='PENDING'
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        process_wallet_list.delay(new_job.id, wallets)

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

    if job.status == 'IN_PROGRESS' and processed_count == job.total_wallets:
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
        # Build structured response with aggregates
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
        return Response(content=json.dumps(response_data, default=str, indent=2), media_type='application/json')
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
