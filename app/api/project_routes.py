"""
Project workspace API — manage named projects with a fixed wallet list
and a history of analysis runs.
"""
import io
import json
from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core import models
from ..core.config import get_db
from ..worker import process_wallet_list

router = APIRouter(prefix="/projects", tags=["Projects"])

# Reuse the same chain / address helpers as routes.py
import re as _re
_EVM_ADDRESS_RE = _re.compile(r'^0x[0-9a-fA-F]{40}$')
_SOLANA_ADDRESS_RE = _re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
SUPPORTED_CHAINS = {"ethereum", "base", "arbitrum", "polygon", "optimism", "bsc", "avalanche", "fantom", "solana", "hedera"}
EVM_MULTI_CHAINS = ["ethereum", "base", "arbitrum", "bsc", "polygon"]


def _parse_chain_list(chain_str: str) -> list[str]:
    s = chain_str.strip().lower()
    if s == "evm":
        return EVM_MULTI_CHAINS
    if "," in s:
        return [c.strip() for c in s.split(",") if c.strip()]
    return [s]


def _validate_wallet(address: str, chain: str) -> str | None:
    if chain not in SUPPORTED_CHAINS:
        return f"Unsupported chain: {chain}"
    if chain == "solana":
        if not _SOLANA_ADDRESS_RE.match(address):
            return f"Invalid Solana address: {address}"
    else:
        if not _EVM_ADDRESS_RE.match(address):
            return f"Invalid EVM address: {address}"
    return None


def _parse_csv(contents: bytes) -> list[dict]:
    """Parse CSV bytes to [{address, chain}] list. Raises HTTPException on invalid input."""
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    if not {'address', 'chain'}.issubset(df.columns):
        raise HTTPException(status_code=400, detail="CSV must have 'address' and 'chain' columns.")

    df['address'] = df['address'].astype(str).str.strip()
    df['chain'] = df['chain'].astype(str).str.strip().str.lower()

    expanded = []
    for _, row in df.iterrows():
        for chain in _parse_chain_list(row['chain']):
            expanded.append({'address': row['address'], 'chain': chain})

    df_exp = pd.DataFrame(expanded).drop_duplicates(subset=['address', 'chain'])
    wallets = df_exp.to_dict('records')

    invalid = []
    for w in wallets:
        err = _validate_wallet(w['address'], w['chain'])
        if err:
            invalid.append(err)
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid addresses: {'; '.join(invalid[:5])}"
            + (f" ... and {len(invalid) - 5} more" if len(invalid) > 5 else ""),
        )

    if not wallets:
        raise HTTPException(status_code=400, detail="No valid wallets found in CSV.")

    return wallets


def _job_summary(job: models.AnalysisJob, db: Session) -> dict:
    """Lightweight summary of one job for the project history list."""
    processed = db.query(func.count(models.WalletAnalysis.id)).filter(
        models.WalletAnalysis.job_id == job.id
    ).scalar() or 0
    status = job.status.value if hasattr(job.status, 'value') else job.status
    return {
        "job_id": job.id,
        "status": status,
        "total_wallets": job.total_wallets,
        "wallets_processed": processed,
        "created_at": str(job.created_at) if job.created_at else None,
        "completed_at": str(job.completed_at) if job.completed_at else None,
        "elapsed_seconds": job.analysis_duration_seconds,
        "result": job.result,
    }


# ---------------------------------------------------------------------------
# List all projects
# ---------------------------------------------------------------------------
@router.get("")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).order_by(models.Project.created_at.desc()).all()
    result = []
    for p in projects:
        last_job = (
            db.query(models.AnalysisJob)
            .filter(models.AnalysisJob.project_id == p.id)
            .order_by(models.AnalysisJob.created_at.desc())
            .first()
        )
        run_count = (
            db.query(func.count(models.AnalysisJob.id))
            .filter(models.AnalysisJob.project_id == p.id)
            .scalar() or 0
        )
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "wallet_count": p.wallet_count,
            "created_at": str(p.created_at) if p.created_at else None,
            "run_count": run_count,
            "last_run_at": str(last_job.created_at) if last_job else None,
            "last_status": (last_job.status.value if hasattr(last_job.status, 'value') else last_job.status) if last_job else None,
        })
    return result


# ---------------------------------------------------------------------------
# Create project
# ---------------------------------------------------------------------------
@router.post("")
def create_project(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Project name is required.")
    existing = db.query(models.Project).filter(models.Project.name == name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"A project named '{name}' already exists.")

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    wallets = _parse_csv(file.file.read())

    project = models.Project(
        name=name,
        description=description.strip() or None,
        wallet_list=json.dumps(wallets),
        wallet_count=len(wallets),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"id": project.id, "name": project.name, "wallet_count": project.wallet_count}


# ---------------------------------------------------------------------------
# Get project detail (info + all runs)
# ---------------------------------------------------------------------------
@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    jobs = (
        db.query(models.AnalysisJob)
        .filter(models.AnalysisJob.project_id == project_id)
        .order_by(models.AnalysisJob.created_at.desc())
        .all()
    )

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "wallet_count": project.wallet_count,
        "created_at": str(project.created_at) if project.created_at else None,
        "runs": [_job_summary(j, db) for j in jobs],
    }


# ---------------------------------------------------------------------------
# Trigger a new analysis run for this project
# ---------------------------------------------------------------------------
@router.post("/{project_id}/run")
def run_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Block if a run is already in progress for this project
    active = (
        db.query(models.AnalysisJob)
        .filter(
            models.AnalysisJob.project_id == project_id,
            models.AnalysisJob.status.in_([models.JobStatus.IN_PROGRESS, models.JobStatus.PENDING]),
        )
        .first()
    )
    if active:
        raise HTTPException(
            status_code=409,
            detail=f"A scan is already running for this project (job {active.id}). Wait for it to finish before starting a new one.",
        )

    wallets = json.loads(project.wallet_list)
    new_job = models.AnalysisJob(
        total_wallets=len(wallets),
        project_name=project.name,
        project_id=project.id,
        status='IN_PROGRESS',
        started_at=datetime.now(timezone.utc),
        pending_wallets=project.wallet_list,
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    chunk_size = 10_000
    for i in range(0, len(wallets), chunk_size):
        process_wallet_list.delay(new_job.id, wallets[i:i + chunk_size])

    return {"job_id": new_job.id, "message": f"Scan started for {len(wallets):,} wallets."}


# ---------------------------------------------------------------------------
# Update project wallet list (re-upload CSV)
# ---------------------------------------------------------------------------
@router.put("/{project_id}")
def update_project(
    project_id: int,
    file: UploadFile = File(None),
    name: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db),
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if name is not None:
        name = name.strip()
        if name and name != project.name:
            existing = db.query(models.Project).filter(models.Project.name == name).first()
            if existing:
                raise HTTPException(status_code=409, detail=f"A project named '{name}' already exists.")
            project.name = name

    if description is not None:
        project.description = description.strip() or None

    if file is not None:
        wallets = _parse_csv(file.file.read())
        project.wallet_list = json.dumps(wallets)
        project.wallet_count = len(wallets)

    db.commit()
    return {"id": project.id, "name": project.name, "wallet_count": project.wallet_count}


# ---------------------------------------------------------------------------
# Delete project (and all its jobs)
# ---------------------------------------------------------------------------
@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    db.delete(project)
    db.commit()
    return {"message": f"Project '{project.name}' deleted."}
