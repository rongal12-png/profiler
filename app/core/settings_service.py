"""
Settings service with DB persistence, versioning, audit logging, and in-memory cache.

Supports two scopes:
  - 'global': applies to all projects (scope_key=None)
  - 'project': per-project overrides (scope_key=project_name)

Effective settings = DEFAULT_SETTINGS <- active global <- active project
"""

import copy
import time
import logging
from sqlalchemy.orm import Session

from .config import SessionLocal
from .models import SettingsVersion, SettingsAuditLog
from .default_settings import DEFAULT_SETTINGS

logger = logging.getLogger(__name__)

# In-memory cache
_cache: dict[str, dict] = {}
_cache_timestamps: dict[str, float] = {}
_CACHE_TTL_SECONDS = 60


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Override values win."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def get_effective_settings(project_name: str | None = None, db: Session | None = None) -> dict:
    """
    Returns the effective settings by merging:
    1. DEFAULT_SETTINGS (hardcoded baseline)
    2. Active global settings from DB (if any)
    3. Active project settings from DB (if project_name provided)

    Uses in-memory cache with 60s TTL.
    """
    cache_key = f"settings:{project_name or '__global__'}"
    now = time.time()

    if cache_key in _cache and (now - _cache_timestamps.get(cache_key, 0)) < _CACHE_TTL_SECONDS:
        return _cache[cache_key]

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        result = copy.deepcopy(DEFAULT_SETTINGS)

        # Layer 2: active global settings
        global_version = (
            db.query(SettingsVersion)
            .filter(SettingsVersion.scope == "global", SettingsVersion.is_active == True, SettingsVersion.scope_key == None)
            .first()
        )
        if global_version and global_version.settings_json:
            result = _deep_merge(result, global_version.settings_json)

        # Layer 3: active project settings
        if project_name:
            project_version = (
                db.query(SettingsVersion)
                .filter(
                    SettingsVersion.scope == "project",
                    SettingsVersion.is_active == True,
                    SettingsVersion.scope_key == project_name,
                )
                .first()
            )
            if project_version and project_version.settings_json:
                result = _deep_merge(result, project_version.settings_json)

        _cache[cache_key] = result
        _cache_timestamps[cache_key] = now
        return result

    finally:
        if close_db:
            db.close()


def create_settings_version(
    db: Session,
    scope: str,
    scope_key: str | None,
    settings_json: dict,
    created_by: str = "admin",
    notes: str | None = None,
) -> SettingsVersion:
    """
    Creates a new settings version, deactivates the previous active version,
    and writes an audit log entry.
    """
    # Find current active version for this scope
    current_active = (
        db.query(SettingsVersion)
        .filter(
            SettingsVersion.scope == scope,
            SettingsVersion.scope_key == scope_key,
            SettingsVersion.is_active == True,
        )
        .first()
    )

    # Determine next version number
    max_version = (
        db.query(SettingsVersion.version)
        .filter(SettingsVersion.scope == scope, SettingsVersion.scope_key == scope_key)
        .order_by(SettingsVersion.version.desc())
        .first()
    )
    next_version = (max_version[0] + 1) if max_version else 1

    previous_json = None
    if current_active:
        previous_json = current_active.settings_json
        current_active.is_active = False
        # Audit log for deactivation
        db.add(SettingsAuditLog(
            settings_version_id=current_active.id,
            action="deactivated",
            changed_by=created_by,
            previous_json=previous_json,
            new_json=previous_json,
        ))

    # Create new version
    new_version = SettingsVersion(
        scope=scope,
        scope_key=scope_key,
        settings_json=settings_json,
        version=next_version,
        is_active=True,
        created_by=created_by,
        notes=notes,
    )
    db.add(new_version)
    db.flush()  # Get the ID

    # Audit log for creation
    db.add(SettingsAuditLog(
        settings_version_id=new_version.id,
        action="created",
        changed_by=created_by,
        previous_json=previous_json,
        new_json=settings_json,
    ))

    db.commit()
    db.refresh(new_version)

    _invalidate_cache()
    logger.info(f"Created settings version {next_version} for scope={scope}, key={scope_key}")
    return new_version


def get_settings_history(
    db: Session,
    scope: str = "global",
    scope_key: str | None = None,
    limit: int = 20,
) -> list[SettingsVersion]:
    """Returns version history for a given scope, newest first."""
    query = db.query(SettingsVersion).filter(
        SettingsVersion.scope == scope,
        SettingsVersion.scope_key == scope_key,
    )
    return query.order_by(SettingsVersion.version.desc()).limit(limit).all()


def activate_settings_version(
    db: Session,
    version_id: int,
    changed_by: str = "admin",
) -> SettingsVersion:
    """Activates a specific settings version and deactivates the current active one."""
    target = db.query(SettingsVersion).filter(SettingsVersion.id == version_id).first()
    if not target:
        raise ValueError(f"Settings version {version_id} not found")

    # Deactivate current active for same scope
    current_active = (
        db.query(SettingsVersion)
        .filter(
            SettingsVersion.scope == target.scope,
            SettingsVersion.scope_key == target.scope_key,
            SettingsVersion.is_active == True,
            SettingsVersion.id != version_id,
        )
        .first()
    )

    if current_active:
        current_active.is_active = False
        db.add(SettingsAuditLog(
            settings_version_id=current_active.id,
            action="deactivated",
            changed_by=changed_by,
            previous_json=current_active.settings_json,
            new_json=current_active.settings_json,
        ))

    target.is_active = True
    db.add(SettingsAuditLog(
        settings_version_id=target.id,
        action="activated",
        changed_by=changed_by,
        previous_json=current_active.settings_json if current_active else None,
        new_json=target.settings_json,
    ))

    db.commit()
    db.refresh(target)

    _invalidate_cache()
    logger.info(f"Activated settings version {target.version} (id={version_id})")
    return target


def _invalidate_cache():
    """Clears the in-memory settings cache."""
    _cache.clear()
    _cache_timestamps.clear()
