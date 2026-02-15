"""
Admin API routes for settings management and sanctions list operations.
Protected by X-API-Key header authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.config import settings, get_db
from ..core import settings_service, sanctions_service
from ..core.models import SanctionsList

admin_router = APIRouter(prefix="/admin", tags=["Admin"])


# --- Auth dependency ---

def require_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    if not settings.ADMIN_API_KEY:
        raise HTTPException(status_code=500, detail="ADMIN_API_KEY not configured on server")
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# --- Request models ---

class SettingsCreateRequest(BaseModel):
    scope: str = "global"
    scope_key: str | None = None
    settings_json: dict
    notes: str | None = None


class SettingsActivateRequest(BaseModel):
    pass  # No body needed, version_id is in path


# --- Settings endpoints ---

@admin_router.get("/settings")
def get_settings(
    scope: str = "global",
    scope_key: str | None = None,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    """Get effective settings (merged defaults <- global <- project)."""
    project_name = scope_key if scope == "project" else None
    effective = settings_service.get_effective_settings(project_name=project_name, db=db)
    return {"scope": scope, "scope_key": scope_key, "settings": effective}


@admin_router.put("/settings")
def create_settings(
    req: SettingsCreateRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    """Create a new settings version (automatically becomes active)."""
    if req.scope not in ("global", "project"):
        raise HTTPException(status_code=400, detail="scope must be 'global' or 'project'")
    if req.scope == "project" and not req.scope_key:
        raise HTTPException(status_code=400, detail="scope_key required for project scope")

    version = settings_service.create_settings_version(
        db=db,
        scope=req.scope,
        scope_key=req.scope_key,
        settings_json=req.settings_json,
        created_by="admin",
        notes=req.notes,
    )
    return {
        "message": "Settings version created",
        "version_id": version.id,
        "version": version.version,
        "is_active": version.is_active,
    }


@admin_router.get("/settings/history")
def get_settings_history(
    scope: str = "global",
    scope_key: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    """Get settings version history for a scope."""
    versions = settings_service.get_settings_history(db=db, scope=scope, scope_key=scope_key, limit=limit)
    return [
        {
            "id": v.id,
            "scope": v.scope,
            "scope_key": v.scope_key,
            "version": v.version,
            "is_active": v.is_active,
            "created_by": v.created_by,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "notes": v.notes,
            "settings_json": v.settings_json,
        }
        for v in versions
    ]


@admin_router.post("/settings/{version_id}/activate")
def activate_settings(
    version_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    """Activate a specific settings version."""
    try:
        version = settings_service.activate_settings_version(db=db, version_id=version_id, changed_by="admin")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "message": "Settings version activated",
        "version_id": version.id,
        "version": version.version,
    }


# --- Sanctions endpoints ---

@admin_router.post("/sanctions/update")
def trigger_sanctions_update(
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    """Trigger an immediate refresh of all enabled sanctions lists."""
    effective = settings_service.get_effective_settings(db=db)
    if not effective["sanctions"]["enabled"]:
        return {"message": "Sanctions screening is disabled in settings"}

    results = sanctions_service.update_all_lists(db=db, settings=effective)
    return {"message": "Sanctions lists update completed", "results": results}


@admin_router.get("/sanctions/status")
def get_sanctions_status(
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    """Show status of all sanctions lists."""
    lists = db.query(SanctionsList).all()
    return [
        {
            "list_name": sl.list_name,
            "status": sl.status,
            "record_count": sl.record_count,
            "last_updated": sl.last_updated.isoformat() if sl.last_updated else None,
            "source_url": sl.source_url,
        }
        for sl in lists
    ]
