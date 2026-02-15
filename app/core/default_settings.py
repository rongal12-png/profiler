"""
Default settings schema for wallet intelligence analysis.

These defaults are used when no DB-persisted settings exist.
All values can be overridden via the admin API (global or per-project scope).
"""

DEFAULT_SETTINGS = {
    "scoring": {
        "weights": {
            "balance": 0.30,
            "activity": 0.15,
            "defi": 0.25,
            "reputation": 0.20,
            "sybil": -0.10,
        },
        "tier_thresholds": {
            "whale": 55,
            "tuna": 30,
        },
    },
    "sanctions": {
        "enabled": True,
        "lists": {
            "ofac_sdn": True,
            "eu_consolidated": True,
            "israel_nbctf": True,
        },
        "action_on_hit": "flag",  # flag | exclude | both
        "auto_update_hours": 24,
    },
    "intelligence": {
        "token_categories_enabled": True,
        "intent_signals_enabled": True,
        "community_score_enabled": True,
        "health_flags_enabled": True,
    },
    "report": {
        "sections": {
            "executive_summary": True,
            "community_score_section": True,
            "product_insights": True,
            "investment_intel_section": True,
            "marketing": True,
            "risk_compliance": True,
            "data_tables": True,
            "recommendations": True,
            "sanctions_section": True,
        },
    },
    "operational": {
        "max_wallets_per_job": 10000,
        "rpc_timeout_seconds": 30,
        "retry_count": 3,
    },
}
