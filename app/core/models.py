from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, JSON, Enum as SQLAlchemyEnum, Index, UniqueConstraint, Text
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class AnalysisJob(Base):
    __tablename__ = 'analysis_jobs'

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    analysis_duration_seconds = Column(Float, nullable=True)
    status = Column(SQLAlchemyEnum(JobStatus), default=JobStatus.PENDING)
    total_wallets = Column(Integer)
    project_name = Column(String, nullable=True)
    result = Column(String, nullable=True)
    pending_wallets = Column(Text, nullable=True)   # JSON list of {address, chain} for resume
    paused_at = Column(DateTime(timezone=True), nullable=True)
    stopped_at = Column(DateTime(timezone=True), nullable=True)

    wallets = relationship("WalletAnalysis", back_populates="job")

class WalletAnalysis(Base):
    __tablename__ = 'wallet_analyses'

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey('analysis_jobs.id'))

    address = Column(String, index=True)
    chain = Column(String, index=True)
    tier = Column(String)
    is_contract = Column(String)
    known_entity_type = Column(String)
    labels = Column(JSON)
    confidence = Column(Float)
    native_balance = Column(Float)
    stable_balances = Column(JSON)
    est_net_worth_usd = Column(Float)
    activity_indicators = Column(JSON)
    product_relevance_score = Column(Float)
    risk_flags = Column(JSON)
    notes = Column(String)
    last_scored_at = Column(DateTime(timezone=True), server_default=func.now())

    # New scoring fields (nullable for backward compat)
    investor_score = Column(Float, nullable=True)
    balance_score = Column(Float, nullable=True)
    activity_score = Column(Float, nullable=True)
    defi_investor_score = Column(Float, nullable=True)
    reputation_score = Column(Float, nullable=True)
    sybil_risk_score = Column(Float, nullable=True)
    persona = Column(String, nullable=True)
    wallet_type = Column(String, nullable=True)  # USER|CEX_EXCHANGE|DEX_ROUTER|BRIDGE|PROTOCOL|CONTRACT|UNKNOWN

    # Sanctions fields (nullable for backward compat)
    sanctions_hit = Column(Boolean, default=False, nullable=True)
    sanctions_list_name = Column(String, nullable=True)
    sanctions_entity_name = Column(String, nullable=True)

    # Intelligence fields (nullable for backward compat)
    token_intelligence = Column(JSON, nullable=True)
    persona_detail = Column(JSON, nullable=True)
    intent_signals = Column(JSON, nullable=True)
    staked_balances = Column(JSON, nullable=True)
    governance_balances = Column(JSON, nullable=True)

    job = relationship("AnalysisJob", back_populates="wallets")


class SettingsVersion(Base):
    __tablename__ = 'settings_versions'
    __table_args__ = (
        UniqueConstraint('scope', 'scope_key', 'version', name='uq_settings_scope_version'),
    )

    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String, nullable=False)  # 'global' or 'project'
    scope_key = Column(String, nullable=True)  # project name for project scope, NULL for global
    settings_json = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String, nullable=False, default='system')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)

    audit_logs = relationship("SettingsAuditLog", back_populates="settings_version")


class SettingsAuditLog(Base):
    __tablename__ = 'settings_audit_log'

    id = Column(Integer, primary_key=True, index=True)
    settings_version_id = Column(Integer, ForeignKey('settings_versions.id'), nullable=False)
    action = Column(String, nullable=False)  # 'created', 'activated', 'deactivated'
    changed_by = Column(String, nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    previous_json = Column(JSON, nullable=True)
    new_json = Column(JSON, nullable=False)

    settings_version = relationship("SettingsVersion", back_populates="audit_logs")


class SanctionsList(Base):
    __tablename__ = 'sanctions_lists'

    id = Column(Integer, primary_key=True, index=True)
    list_name = Column(String, nullable=False, unique=True)  # ofac_sdn, eu_consolidated, israel_nbctf
    last_updated = Column(DateTime(timezone=True), nullable=True)
    record_count = Column(Integer, default=0)
    source_url = Column(String, nullable=False)
    file_hash = Column(String, nullable=True)
    status = Column(String, nullable=False, default='pending')  # pending, active, updating, error

    addresses = relationship("SanctionsAddress", back_populates="sanctions_list", cascade="all, delete-orphan")


class SanctionsAddress(Base):
    __tablename__ = 'sanctions_addresses'
    __table_args__ = (
        Index('ix_sanctions_addresses_address', 'address'),
    )

    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(Integer, ForeignKey('sanctions_lists.id'), nullable=False)
    address = Column(String, nullable=False)
    entity_name = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    source_entry_id = Column(String, nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    sanctions_list = relationship("SanctionsList", back_populates="addresses")
