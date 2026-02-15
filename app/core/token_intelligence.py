"""
Token Intelligence Module — Analyzes wallet token holdings to produce
categorized breakdown, concentration metrics, and investment signals.
"""


def analyze_token_holdings(
    native_balance_usd: float,
    stable_balances: list[dict],
    top_token_balances: list[dict],
    staked_token_balances: list[dict],
    governance_token_balances: list[dict],
) -> dict:
    """
    Categorize and analyze a wallet's token holdings.

    Each balance list contains dicts with at least: {symbol, amount}
    and optionally {usd}.

    Returns a dict with categories, concentration, and signal flags.
    """
    # Calculate USD values per category
    native_usd = float(native_balance_usd)
    stable_usd = sum(float(b.get("usd", b.get("amount", 0))) for b in stable_balances)
    staked_usd = sum(float(b.get("usd", b.get("amount", 0))) for b in staked_token_balances)
    governance_usd = sum(float(b.get("usd", b.get("amount", 0))) for b in governance_token_balances)
    other_usd = sum(float(b.get("usd", b.get("amount", 0))) for b in top_token_balances)

    total_usd = native_usd + stable_usd + staked_usd + governance_usd + other_usd
    if total_usd <= 0:
        total_usd = 0.01  # avoid division by zero

    def pct(val):
        return round(val / total_usd, 4) if total_usd > 0 else 0.0

    categories = {
        "native": {"usd": round(native_usd, 2), "pct": pct(native_usd)},
        "stablecoin": {"usd": round(stable_usd, 2), "pct": pct(stable_usd)},
        "staked": {
            "usd": round(staked_usd, 2),
            "pct": pct(staked_usd),
            "tokens": [b.get("symbol", "?") for b in staked_token_balances if float(b.get("amount", 0)) > 0],
        },
        "governance": {
            "usd": round(governance_usd, 2),
            "pct": pct(governance_usd),
            "tokens": [b.get("symbol", "?") for b in governance_token_balances if float(b.get("amount", 0)) > 0],
        },
        "other": {
            "usd": round(other_usd, 2),
            "pct": pct(other_usd),
            "tokens": [b.get("symbol", "?") for b in top_token_balances if float(b.get("amount", 0)) > 0],
        },
    }

    # Concentration: Herfindahl index across categories
    cat_pcts = [pct(native_usd), pct(stable_usd), pct(staked_usd), pct(governance_usd), pct(other_usd)]
    concentration = round(sum(p ** 2 for p in cat_pcts), 4)

    # Token diversity: count of distinct non-zero token holdings
    token_diversity = 0
    if native_usd > 0:
        token_diversity += 1
    token_diversity += sum(1 for b in stable_balances if float(b.get("amount", 0)) > 0)
    token_diversity += sum(1 for b in staked_token_balances if float(b.get("amount", 0)) > 0)
    token_diversity += sum(1 for b in governance_token_balances if float(b.get("amount", 0)) > 0)
    token_diversity += sum(1 for b in top_token_balances if float(b.get("amount", 0)) > 0)

    stablecoin_share = pct(stable_usd)
    staked_share = pct(staked_usd)
    has_staking = staked_usd > 0
    has_governance = governance_usd > 0

    # Signal: dry powder = high stablecoin with low other activity tokens
    dry_powder_signal = stablecoin_share > 0.5 and total_usd > 500

    # Signal: long-term = significant staking positions
    long_term_signal = staked_share > 0.2 and total_usd > 100

    return {
        "categories": categories,
        "total_usd": round(total_usd, 2),
        "concentration": concentration,
        "stablecoin_share": stablecoin_share,
        "staked_share": staked_share,
        "token_diversity": token_diversity,
        "has_staking_positions": has_staking,
        "has_governance_tokens": has_governance,
        "dry_powder_signal": dry_powder_signal,
        "long_term_signal": long_term_signal,
    }
