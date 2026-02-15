"""
Multi-component wallet scoring model for launchpad investor intelligence.

Components (each 0-100):
  - balance_score: USD net worth
  - activity_score: tx count, recency, diversity
  - defi_investor_score: DeFi protocol interactions
  - reputation_score: VC/KOL labels, known smart money (penalty for infra)
  - sybil_risk_score: bot/sybil likelihood (higher = more suspicious)

Final investor_score: weighted composite (0-100)
Tier: Whale / Tuna / Fish / Infra
Persona: Trader / Staker / Farmer / Long-term Holder / Airdrop Hunter / Infra
"""

import math


def compute_balance_score(est_net_worth_usd: float, stable_usd_total: float) -> float:
    """Score based on total USD value. Log-scaled to avoid whale domination."""
    total = est_net_worth_usd + stable_usd_total
    if total <= 0:
        return 0.0
    # log10(100) = 2 -> score ~20, log10(10000) = 4 -> ~40, log10(1M) = 6 -> ~60, log10(100M) = 8 -> ~80
    raw = math.log10(max(total, 1)) * 10
    return min(round(raw, 1), 100.0)


def compute_activity_score(tx_count: int, is_contract: bool) -> float:
    """Score based on transaction count as a proxy for engagement."""
    if is_contract:
        return 0.0
    if tx_count <= 0:
        return 0.0
    # log2 scale: 1 tx -> ~0, 10 tx -> ~33, 100 tx -> ~66, 1000+ -> ~100
    raw = math.log2(max(tx_count, 1)) * 10
    return min(round(raw, 1), 100.0)


def compute_defi_investor_score(
    tx_count: int,
    stable_usd_total: float,
    top_token_count: int,
    est_net_worth_usd: float,
) -> float:
    """
    Heuristic for DeFi/investor behavior.
    - Holding multiple token types suggests active investing
    - High stablecoin ratio suggests dry powder / ready to invest
    - Moderate tx count with holdings suggests real usage
    """
    score = 0.0

    # Token diversity (holding multiple tokens = investor signal)
    if top_token_count >= 3:
        score += 30
    elif top_token_count >= 1:
        score += 15

    # Stablecoin dry powder
    if stable_usd_total >= 100_000:
        score += 30
    elif stable_usd_total >= 10_000:
        score += 20
    elif stable_usd_total >= 1_000:
        score += 10

    # Activity level with holdings (not just an empty active wallet)
    if tx_count >= 50 and est_net_worth_usd >= 1_000:
        score += 25
    elif tx_count >= 10 and est_net_worth_usd >= 100:
        score += 15
    elif tx_count >= 5:
        score += 5

    return min(round(score, 1), 100.0)


def compute_reputation_score(
    known_entity_type: str,
    labels: list[str],
    label_types: list[str],
) -> float:
    """
    Score based on identity.
    High for: VC, KOL, smart money
    Neutral for: unknown users
    Negative for: exchange, bridge, protocol (infra)
    """
    score = 50.0  # baseline for unknown users

    # Check label types from our known_labels.json
    for lt in label_types:
        if lt in ("vc", "smart_money"):
            score = max(score, 90.0)
        elif lt == "kol":
            score = max(score, 85.0)
        elif lt in ("exchange", "bridge", "dex_router"):
            score = min(score, 10.0)
        elif lt == "protocol":
            score = min(score, 15.0)

    # Fallback to known_entity_type from chain analysis
    if known_entity_type in ("exchange", "bridge", "protocol", "dex_router"):
        score = min(score, 10.0)
    elif known_entity_type == "contract":
        score = min(score, 20.0)

    # Boost for "High Activity" label
    if "High Activity" in labels:
        score = min(score + 10, 100.0)

    return round(score, 1)


def compute_sybil_risk_score(
    tx_count: int,
    est_net_worth_usd: float,
    is_contract: bool,
    known_entity_type: str,
) -> float:
    """
    Higher score = more suspicious.
    Sybil indicators: low balance, very high or very low tx count, contract addresses.
    """
    score = 0.0

    # Contracts pretending to be users
    if is_contract and known_entity_type == "user":
        score += 40

    # Very low balance with some activity (airdrop farming pattern)
    if est_net_worth_usd < 10 and tx_count > 20:
        score += 30
    elif est_net_worth_usd < 100 and tx_count > 100:
        score += 25

    # Zero balance, zero activity (dust/dead wallet)
    if est_net_worth_usd < 1 and tx_count <= 1:
        score += 20

    # Known infra is not sybil, it's just infra
    if known_entity_type in ("exchange", "bridge", "protocol", "dex_router"):
        score = max(score - 20, 0)

    return min(round(score, 1), 100.0)


def compute_investor_score(
    balance_score: float,
    activity_score: float,
    defi_investor_score: float,
    reputation_score: float,
    sybil_risk_score: float,
    weights: dict | None = None,
) -> float:
    """Weighted composite investor quality score. Accepts optional weights dict."""
    w = weights or {"balance": 0.30, "activity": 0.15, "defi": 0.25, "reputation": 0.20, "sybil": -0.10}
    # Cast weights to float in case they come from DB as Decimal
    raw = (
        balance_score * float(w.get("balance", 0.30))
        + activity_score * float(w.get("activity", 0.15))
        + defi_investor_score * float(w.get("defi", 0.25))
        + reputation_score * float(w.get("reputation", 0.20))
        + sybil_risk_score * float(w.get("sybil", -0.10))  # negative weight = penalty
    )
    return min(max(round(raw, 1), 0.0), 100.0)


def determine_tier(
    investor_score: float,
    known_entity_type: str,
    is_contract: bool,
    label_types: list[str],
    thresholds: dict | None = None,
) -> str:
    """
    Whale: high investor_score OR VC/KOL labeled OR high defi+launchpad investing
    Tuna: medium investor_score with real activity
    Fish: low investor_score or low engagement
    Infra: exchange/bridge/protocol/contract
    Accepts optional thresholds dict with 'whale' and 'tuna' keys.
    """
    t = thresholds or {"whale": 55, "tuna": 30}
    # Cast thresholds to float in case they come from DB as Decimal
    whale_threshold = float(t.get("whale", 55))
    tuna_threshold = float(t.get("tuna", 30))

    # Infra wallets are always Infra
    if known_entity_type in ("exchange", "bridge", "protocol", "dex_router"):
        return "Infra"
    if is_contract:
        return "Infra"

    # VC/KOL always at least Whale
    for lt in label_types:
        if lt in ("vc", "kol", "smart_money"):
            return "Whale"

    if investor_score >= whale_threshold:
        return "Whale"
    elif investor_score >= tuna_threshold:
        return "Tuna"
    else:
        return "Fish"


def determine_persona(
    tx_count: int,
    est_net_worth_usd: float,
    stable_usd_total: float,
    is_contract: bool,
    known_entity_type: str,
    sybil_risk_score: float,
    staked_share: float = 0.0,
    has_governance_tokens: bool = False,
) -> str:
    """Assign a primary persona based on behavioral heuristics."""
    if is_contract or known_entity_type in ("exchange", "bridge", "protocol", "dex_router"):
        return "Infra"

    if sybil_risk_score >= 50:
        return "Airdrop Hunter"

    total_value = est_net_worth_usd + stable_usd_total
    stable_ratio = stable_usd_total / total_value if total_value > 0 else 0

    # Newcomer: very low activity + small value
    if tx_count <= 5 and total_value < 1000 and total_value > 0:
        return "Newcomer"

    # Staker: significant staked positions
    if staked_share > 0.3 and total_value > 100:
        return "Staker"

    # High stablecoin ratio + low activity = holder waiting to deploy
    if stable_ratio > 0.7 and tx_count < 20 and total_value > 1000:
        return "Long-term Holder"

    # High activity + high value = trader
    if tx_count > 100 and total_value > 10_000:
        return "Trader"

    # Moderate activity + moderate value = farmer/staker
    if tx_count > 30 and total_value > 1_000:
        return "Farmer"

    # Low activity + some value = holder
    if tx_count < 10 and total_value > 100:
        return "Long-term Holder"

    # High activity + low value = possible airdrop hunter
    if tx_count > 50 and total_value < 500:
        return "Airdrop Hunter"

    return "Trader"


def determine_persona_detail(
    tx_count: int,
    est_net_worth_usd: float,
    stable_usd_total: float,
    is_contract: bool,
    known_entity_type: str,
    sybil_risk_score: float,
    staked_share: float = 0.0,
    has_governance_tokens: bool = False,
    token_diversity: int = 0,
) -> dict:
    """
    Assign a persona with confidence score and evidence signals.
    Returns: {primary, confidence, evidence, secondary}
    """
    primary = determine_persona(
        tx_count, est_net_worth_usd, stable_usd_total,
        is_contract, known_entity_type, sybil_risk_score,
        staked_share, has_governance_tokens,
    )

    evidence = []
    confidence = 0.5  # baseline
    secondary = None
    total_value = est_net_worth_usd + stable_usd_total
    stable_ratio = stable_usd_total / total_value if total_value > 0 else 0

    if primary == "Infra":
        confidence = 0.95
        evidence.append(f"Classified as {known_entity_type}")
        if is_contract:
            evidence.append("Smart contract address")
    elif primary == "Airdrop Hunter":
        confidence = 0.7 if sybil_risk_score >= 60 else 0.55
        evidence.append(f"Sybil risk score: {sybil_risk_score:.0f}")
        if total_value < 100 and tx_count > 20:
            evidence.append(f"Low value (${total_value:,.0f}) with {tx_count} txs")
            confidence += 0.1
    elif primary == "Newcomer":
        confidence = 0.75
        evidence.append(f"Only {tx_count} transactions")
        if total_value > 0:
            evidence.append(f"Small portfolio: ${total_value:,.0f}")
        secondary = "Long-term Holder" if stable_ratio > 0.5 else "Trader"
    elif primary == "Staker":
        confidence = 0.8 if staked_share > 0.5 else 0.65
        evidence.append(f"{staked_share:.0%} of portfolio staked")
        if has_governance_tokens:
            evidence.append("Holds governance tokens")
            confidence = min(confidence + 0.1, 0.95)
        secondary = "Long-term Holder"
    elif primary == "Long-term Holder":
        confidence = 0.7
        if stable_ratio > 0.7:
            evidence.append(f"High stablecoin ratio ({stable_ratio:.0%})")
            confidence += 0.1
        if tx_count < 10:
            evidence.append(f"Low activity ({tx_count} txs)")
        secondary = "Staker" if staked_share > 0.1 else None
    elif primary == "Trader":
        confidence = 0.6
        if tx_count > 100:
            evidence.append(f"High activity ({tx_count} txs)")
            confidence += 0.1
        if total_value > 10_000:
            evidence.append(f"Significant portfolio (${total_value:,.0f})")
            confidence += 0.05
        secondary = "Farmer" if token_diversity >= 4 else None
    elif primary == "Farmer":
        confidence = 0.6
        evidence.append(f"Moderate activity ({tx_count} txs)")
        if total_value > 1_000:
            evidence.append(f"Active portfolio (${total_value:,.0f})")
        if token_diversity >= 3:
            evidence.append(f"Diversified ({token_diversity} tokens)")
            confidence += 0.1
        secondary = "Trader" if tx_count > 80 else "Staker" if staked_share > 0.1 else None

    confidence = round(min(confidence, 0.95), 2)

    return {
        "primary": primary,
        "confidence": confidence,
        "evidence": evidence,
        "secondary": secondary,
    }


def score_wallet(
    est_net_worth_usd: float,
    stable_usd_total: float,
    tx_count: int,
    is_contract: bool,
    known_entity_type: str,
    labels: list[str],
    label_types: list[str],
    top_token_count: int = 0,
    scoring_settings: dict | None = None,
    token_intel: dict | None = None,
) -> dict:
    """
    Main entry point: compute all scores, tier, and persona for a wallet.
    Returns a dict with all scoring fields.

    Optional scoring_settings dict can override weights and tier thresholds:
      {"weights": {...}, "tier_thresholds": {...}}
    Optional token_intel dict provides staked_share, has_governance_tokens, token_diversity.
    """
    weights = None
    thresholds = None
    if scoring_settings:
        weights = scoring_settings.get("weights")
        thresholds = scoring_settings.get("tier_thresholds")

    balance = compute_balance_score(est_net_worth_usd, stable_usd_total)
    activity = compute_activity_score(tx_count, is_contract)
    defi = compute_defi_investor_score(tx_count, stable_usd_total, top_token_count, est_net_worth_usd)
    reputation = compute_reputation_score(known_entity_type, labels, label_types)
    sybil = compute_sybil_risk_score(tx_count, est_net_worth_usd, is_contract, known_entity_type)

    investor = compute_investor_score(balance, activity, defi, reputation, sybil, weights=weights)
    tier = determine_tier(investor, known_entity_type, is_contract, label_types, thresholds=thresholds)

    # Extract token intelligence data for persona detection
    staked_share = 0.0
    has_governance = False
    token_diversity = 0
    if token_intel:
        staked_share = token_intel.get("staked_share", 0.0)
        has_governance = token_intel.get("has_governance_tokens", False)
        token_diversity = token_intel.get("token_diversity", 0)

    persona = determine_persona(
        tx_count, est_net_worth_usd, stable_usd_total,
        is_contract, known_entity_type, sybil,
        staked_share=staked_share, has_governance_tokens=has_governance,
    )
    persona_detail = determine_persona_detail(
        tx_count, est_net_worth_usd, stable_usd_total,
        is_contract, known_entity_type, sybil,
        staked_share=staked_share, has_governance_tokens=has_governance,
        token_diversity=token_diversity,
    )

    return {
        "investor_score": investor,
        "balance_score": balance,
        "activity_score": activity,
        "defi_investor_score": defi,
        "reputation_score": reputation,
        "sybil_risk_score": sybil,
        "tier": tier,
        "persona": persona,
        "persona_detail": persona_detail,
        "product_relevance_score": investor,  # alias for backward compat
    }
