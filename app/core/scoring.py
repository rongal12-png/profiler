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
    staked_share: float = 0.0,
    has_governance_tokens: bool = False,
) -> float:
    """
    Heuristic for DeFi/investor behavior.
    - Holding multiple token types suggests active investing
    - High stablecoin ratio suggests dry powder / ready to invest
    - Moderate tx count with holdings suggests real usage
    - Staking and governance participation are strong DeFi commitment signals
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

    # Staking: long-term DeFi commitment signal — illiquid position = conviction
    if staked_share >= 0.5:
        score += 20
    elif staked_share >= 0.2:
        score += 12
    elif staked_share >= 0.05:
        score += 5

    # Governance: holding governance tokens signals protocol-level engagement
    if has_governance_tokens:
        score += 15

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
    wallet_age_days: int = 0,
) -> float:
    """
    Higher score = more suspicious.

    Sybil indicators (additive):
    - Contract masquerading as user: +40
    - Classic airdrop farming: low balance + high tx count
    - Gas-only wallet: near-zero native balance with meaningful tx activity (funded just enough to interact)
    - Round-number tx count: farmers often hit exact targets (10, 20, 50 txs exactly)
    - Age signal (if available): very new wallet with burst of activity
    """
    score = 0.0

    # Contracts pretending to be users
    if is_contract and known_entity_type == "user":
        score += 40

    # Classic airdrop farming: very low value relative to activity
    if est_net_worth_usd < 10 and tx_count > 20:
        score += 30
    elif est_net_worth_usd < 100 and tx_count > 100:
        score += 25

    # Gas-only wallet: funded with just enough to make transactions — no real holdings
    # Distinct from the dust check below: these wallets ARE active, just perpetually empty
    if est_net_worth_usd < 2 and tx_count >= 5:
        score += 20

    # Zero balance, zero activity (dust/dead wallet)
    if est_net_worth_usd < 1 and tx_count <= 1:
        score += 20

    # Round-number tx pattern: airdrop hunters often hit exact targets before stopping
    # Only suspicious when combined with low holdings (not for legitimate active users)
    if est_net_worth_usd < 200 and tx_count in {5, 10, 15, 20, 25, 30, 50, 100}:
        score += 10

    # Wallet age signal: burst activity on a very new wallet is suspicious
    # Only apply when age data is available (wallet_age_days > 0)
    if wallet_age_days > 0:
        if wallet_age_days < 30 and tx_count > 15:
            score += 25  # very new + many txs = likely sybil burst
        elif wallet_age_days < 90 and tx_count > 50:
            score += 12  # young wallet + high activity

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
    wallet_type: str = "USER",
    est_net_worth_usd: float = 0.0,
) -> str:
    """
    Whale: high investor_score OR VC/KOL labeled OR capital >= $1M
    Tuna: medium investor_score OR capital >= $100K
    Fish: low investor_score or low engagement
    Infra: exchange/bridge/protocol/contract
    Accepts optional thresholds dict with 'whale' and 'tuna' keys.
    """
    t = thresholds or {"whale": 55, "tuna": 30}
    # Cast thresholds to float in case they come from DB as Decimal
    whale_threshold = float(t.get("whale", 55))
    tuna_threshold = float(t.get("tuna", 30))

    # Non-USER wallet types are always Infra (CEX/DEX/Bridge/Protocol never count as Whale)
    if wallet_type in ("CEX_EXCHANGE", "DEX_ROUTER", "BRIDGE", "PROTOCOL", "CONTRACT"):
        return "Infra"
    # Infra wallets are always Infra
    if known_entity_type in ("exchange", "bridge", "protocol", "dex_router"):
        return "Infra"
    if is_contract:
        return "Infra"

    # VC/KOL always at least Whale
    for lt in label_types:
        if lt in ("vc", "kol", "smart_money"):
            return "Whale"

    # Capital-based floors: large capital is always Whale/Tuna regardless of score
    usd = float(est_net_worth_usd or 0)
    if usd >= 1_000_000:
        return "Whale"
    if usd >= 100_000:
        return "Tuna" if investor_score < whale_threshold else "Whale"

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
    """
    Assign a primary persona based on behavioral heuristics.

    Priority order (highest specificity first):
    1. Infra — contract or known infra entity
    2. Airdrop Hunter — confirmed sybil signal
    3. Newcomer — very new/small wallet
    4. Staker — staking is primary activity (any meaningful staked share)
    5. Long-term Holder — low activity, holds value
    6. Trader — high activity + meaningful value
    7. Farmer — moderate activity across protocols
    8. Airdrop Hunter (lower confidence) — high activity + low value
    9. Long-term Holder (default for moderate-value, low-activity)
    """
    if is_contract or known_entity_type in ("exchange", "bridge", "protocol", "dex_router"):
        return "Infra"

    if sybil_risk_score >= 50:
        return "Airdrop Hunter"

    total_value = est_net_worth_usd + stable_usd_total
    stable_ratio = stable_usd_total / total_value if total_value > 0 else 0

    # Newcomer: very low activity + small wallet (raised threshold from $1K to $5K)
    if tx_count <= 5 and total_value < 5_000 and total_value > 0:
        return "Newcomer"

    # Staker: any meaningful staked share (lowered from 0.3 to 0.1, enough to signal commitment)
    # Requires enough value to be a real position, not just dust
    if staked_share >= 0.1 and total_value > 500:
        return "Staker"

    # High stablecoin dry powder + low activity = capital allocator waiting to deploy
    # Use governance/staking as a tiebreaker: real holders often have both
    if stable_ratio > 0.7 and tx_count < 30 and total_value > 1_000:
        return "Long-term Holder"

    # High activity + meaningful value = active trader
    if tx_count > 100 and total_value > 5_000:
        return "Trader"

    # Moderate-high activity + moderate value = DeFi farmer
    if tx_count > 30 and total_value > 1_000:
        return "Farmer"

    # High activity + low value = airdrop hunting (lower confidence than score>=50)
    if tx_count > 50 and total_value < 500:
        return "Airdrop Hunter"

    # Low activity + some value = passive holder
    if tx_count < 15 and total_value > 200:
        return "Long-term Holder"

    # Default: moderate engagement without a dominant signal
    # Use value as tiebreaker — higher value = more likely a real investor
    if total_value > 2_000:
        return "Farmer"
    return "Newcomer"


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
        confidence = 0.85 if staked_share >= 0.5 else 0.75 if staked_share >= 0.2 else 0.60
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
    wallet_type: str = "USER",
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
    defi = compute_defi_investor_score(
        tx_count, stable_usd_total, top_token_count, est_net_worth_usd,
        staked_share=float(token_intel.get("staked_share", 0) or 0) if token_intel else 0.0,
        has_governance_tokens=bool(token_intel.get("has_governance_tokens", False)) if token_intel else False,
    )
    reputation = compute_reputation_score(known_entity_type, labels, label_types)
    sybil = compute_sybil_risk_score(tx_count, est_net_worth_usd, is_contract, known_entity_type)

    investor = compute_investor_score(balance, activity, defi, reputation, sybil, weights=weights)
    tier = determine_tier(investor, known_entity_type, is_contract, label_types, thresholds=thresholds, wallet_type=wallet_type, est_net_worth_usd=est_net_worth_usd)

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
