"""
Investment Intent Signals Module — Infers investment readiness and behavior
from wallet balance data (no transaction history required).
"""


def detect_intent_signals(
    token_intel: dict,
    tx_count: int,
    persona: str,
    tier: str,
) -> dict:
    """
    Detect investment intent signals from token intelligence and wallet metadata.

    Returns a dict with signals list, investment_readiness level, and
    estimated deployable USD.
    """
    signals = []
    total_usd = token_intel.get("total_usd", 0)
    stablecoin_share = token_intel.get("stablecoin_share", 0)
    staked_share = token_intel.get("staked_share", 0)
    stable_usd = token_intel.get("categories", {}).get("stablecoin", {}).get("usd", 0)
    native_usd = token_intel.get("categories", {}).get("native", {}).get("usd", 0)
    token_diversity = token_intel.get("token_diversity", 0)
    concentration = token_intel.get("concentration", 1.0)
    has_staking = token_intel.get("has_staking_positions", False)
    has_governance = token_intel.get("has_governance_tokens", False)

    # 1. Dry powder — high stablecoin holdings = ready to deploy capital
    if stablecoin_share > 0.6 and stable_usd > 10_000:
        signals.append({
            "signal": "dry_powder",
            "strength": "strong",
            "detail": f"${stable_usd:,.0f} in stablecoins ({stablecoin_share:.0%} of portfolio)",
        })
    elif stablecoin_share > 0.4 and stable_usd > 1_000:
        signals.append({
            "signal": "dry_powder",
            "strength": "moderate",
            "detail": f"${stable_usd:,.0f} in stablecoins ({stablecoin_share:.0%} of portfolio)",
        })

    # 2. Long-term commitment — staked assets = not planning to exit
    if staked_share > 0.3:
        signals.append({
            "signal": "long_term_commitment",
            "strength": "strong",
            "detail": f"{staked_share:.0%} of portfolio in staked assets",
        })
    elif has_staking and staked_share > 0.1:
        signals.append({
            "signal": "long_term_commitment",
            "strength": "moderate",
            "detail": f"{staked_share:.0%} in staked assets ({', '.join(token_intel.get('categories', {}).get('staked', {}).get('tokens', []))})",
        })

    # 3. Governance participation — active DeFi participant
    if has_governance:
        gov_tokens = token_intel.get("categories", {}).get("governance", {}).get("tokens", [])
        signals.append({
            "signal": "governance_participant",
            "strength": "moderate" if len(gov_tokens) >= 2 else "weak",
            "detail": f"Holds governance tokens: {', '.join(gov_tokens)}",
        })

    # 4. Diversified portfolio — experienced investor
    if token_diversity >= 5:
        signals.append({
            "signal": "diversified_portfolio",
            "strength": "strong",
            "detail": f"{token_diversity} distinct token holdings across categories",
        })
    elif token_diversity >= 3:
        signals.append({
            "signal": "diversified_portfolio",
            "strength": "moderate",
            "detail": f"{token_diversity} distinct token holdings",
        })

    # 5. Concentrated bet — single category dominance
    if concentration > 0.8 and total_usd > 1_000:
        # Find which category dominates
        cats = token_intel.get("categories", {})
        dominant = max(cats.items(), key=lambda x: x[1].get("pct", 0)) if cats else ("unknown", {})
        signals.append({
            "signal": "concentrated_position",
            "strength": "strong",
            "detail": f"{dominant[1].get('pct', 0):.0%} concentrated in {dominant[0]}",
        })

    # 6. Active trader signal — high tx count + significant value
    if tx_count > 100 and total_usd > 10_000:
        signals.append({
            "signal": "active_trader",
            "strength": "strong",
            "detail": f"{tx_count} transactions with ${total_usd:,.0f} portfolio",
        })
    elif tx_count > 50 and total_usd > 1_000:
        signals.append({
            "signal": "active_trader",
            "strength": "moderate",
            "detail": f"{tx_count} transactions with ${total_usd:,.0f} portfolio",
        })

    # Determine investment readiness
    strong_count = sum(1 for s in signals if s["strength"] == "strong")
    moderate_count = sum(1 for s in signals if s["strength"] == "moderate")
    score = strong_count * 3 + moderate_count * 1

    if score >= 5 or (tier == "Whale" and score >= 2):
        investment_readiness = "high"
    elif score >= 2:
        investment_readiness = "medium"
    else:
        investment_readiness = "low"

    # Estimated deployable USD = stablecoins + liquid native
    estimated_deployable_usd = round(stable_usd + native_usd, 2)

    return {
        "signals": signals,
        "investment_readiness": investment_readiness,
        "estimated_deployable_usd": estimated_deployable_usd,
    }
