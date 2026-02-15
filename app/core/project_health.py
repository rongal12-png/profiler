"""
Project Health & Community Quality Module — Computes project-level aggregate
scores, health flags, and concentration metrics from the wallet set.
"""
import math
import numpy as np


def compute_community_quality_score(df) -> dict:
    """
    Compute a project-level community quality score (0-100).

    Components (weighted):
    - User ratio (30%): % of wallets that are real users
    - Investor quality (25%): average investor_score of users
    - Diversity (15%): persona distribution evenness (Shannon entropy)
    - Whale presence (15%): whale count weighted by quality
    - Health signals (15%): inverse of sybil ratio + sanctions ratio
    """
    total = len(df)
    if total == 0:
        return {"score": 0, "grade": "F", "components": {}, "narrative": "No wallets to analyze."}

    # User ratio component (0-100)
    user_count = len(df[df['wallet_type'] == 'USER'])
    user_ratio = user_count / total
    user_ratio_score = min(user_ratio * 100 / 0.7, 100)  # 70%+ users = perfect score

    # Investor quality component (0-100) — average investor_score of users
    users_df = df[df['wallet_type'] == 'USER']
    if len(users_df) > 0:
        investor_quality_score = float(users_df['investor_score'].mean())
    else:
        investor_quality_score = 0.0

    # Diversity component (0-100) — Shannon entropy of persona distribution
    persona_counts = df['persona'].value_counts()
    if len(persona_counts) > 1:
        proportions = persona_counts / persona_counts.sum()
        entropy = -sum(p * math.log2(p) for p in proportions if p > 0)
        max_entropy = math.log2(len(persona_counts))
        diversity_score = (entropy / max_entropy) * 100 if max_entropy > 0 else 0
    else:
        diversity_score = 0.0

    # Whale presence component (0-100)
    whale_count = len(df[df['tier'] == 'Whale'])
    if total >= 10:
        whale_pct = whale_count / total
        # Sweet spot: 5-15% whales is ideal
        if 0.05 <= whale_pct <= 0.15:
            whale_score = 100.0
        elif whale_pct < 0.05:
            whale_score = whale_pct / 0.05 * 100
        else:  # too whale-heavy
            whale_score = max(100 - (whale_pct - 0.15) * 300, 20)
    else:
        whale_score = min(whale_count * 30, 100)

    # Health signals component (0-100) — inverse of bad signals
    sybil_count = len(df[df['sybil_risk_score'] >= 40]) if 'sybil_risk_score' in df.columns else 0
    sanctions_count = len(df[df['sanctions_hit'] == True]) if 'sanctions_hit' in df.columns else 0
    sybil_ratio = sybil_count / total
    sanctions_ratio = sanctions_count / total
    health_score = max(100 - sybil_ratio * 200 - sanctions_ratio * 500, 0)

    # Weighted composite
    score = (
        user_ratio_score * 0.30
        + investor_quality_score * 0.25
        + diversity_score * 0.15
        + whale_score * 0.15
        + health_score * 0.15
    )
    score = round(min(max(score, 0), 100), 1)

    # Grade mapping
    grade = _score_to_grade(score)

    # Narrative
    narrative = _build_quality_narrative(score, grade, user_ratio, investor_quality_score, whale_count, sybil_count)

    return {
        "score": score,
        "grade": grade,
        "components": {
            "user_ratio": {"score": round(user_ratio_score, 1), "weight": 0.30, "detail": f"{user_ratio:.1%} real users"},
            "investor_quality": {"score": round(investor_quality_score, 1), "weight": 0.25, "detail": f"Avg score {investor_quality_score:.1f}"},
            "diversity": {"score": round(diversity_score, 1), "weight": 0.15, "detail": f"{len(persona_counts)} persona types"},
            "whale_presence": {"score": round(whale_score, 1), "weight": 0.15, "detail": f"{whale_count} whales"},
            "health": {"score": round(health_score, 1), "weight": 0.15, "detail": f"{sybil_count} sybil, {sanctions_count} sanctions"},
        },
        "narrative": narrative,
    }


def _score_to_grade(score: float) -> str:
    if score >= 90: return "A+"
    if score >= 85: return "A"
    if score >= 80: return "A-"
    if score >= 75: return "B+"
    if score >= 70: return "B"
    if score >= 65: return "B-"
    if score >= 60: return "C+"
    if score >= 55: return "C"
    if score >= 50: return "C-"
    if score >= 40: return "D"
    return "F"


def _build_quality_narrative(score, grade, user_ratio, avg_investor, whale_count, sybil_count) -> str:
    parts = []
    if score >= 70:
        parts.append(f"This community scores {score}/100 (Grade {grade}), indicating a healthy and engaged wallet base.")
    elif score >= 50:
        parts.append(f"This community scores {score}/100 (Grade {grade}), showing moderate quality with room for improvement.")
    else:
        parts.append(f"This community scores {score}/100 (Grade {grade}), suggesting an early-stage or low-quality wallet base that needs attention.")

    if user_ratio < 0.5:
        parts.append("A low proportion of real users vs infrastructure wallets limits the signal quality.")
    if avg_investor < 25:
        parts.append("Average investor quality is low — the community is mostly small or new participants.")
    elif avg_investor > 50:
        parts.append("Average investor quality is strong — experienced DeFi participants are well-represented.")
    if whale_count == 0:
        parts.append("No whale-tier wallets detected — attracting institutional or high-value participants should be a priority.")
    if sybil_count > 0:
        parts.append(f"{sybil_count} wallets show sybil/farming patterns that may dilute community quality metrics.")

    return " ".join(parts)


def compute_health_flags(df) -> list[dict]:
    """
    Compute project-level health flags (red/yellow/green severity).
    """
    flags = []
    total = len(df)
    if total == 0:
        return flags

    total_usd = df['est_net_worth_usd'].sum()

    # 1. Exchange-heavy: >30% of value in CEX wallets
    cex_df = df[df['wallet_type'] == 'CEX_EXCHANGE']
    if len(cex_df) > 0 and total_usd > 0:
        cex_value_pct = cex_df['est_net_worth_usd'].sum() / total_usd
        if cex_value_pct > 0.3:
            flags.append({
                "flag": "exchange_heavy",
                "severity": "red" if cex_value_pct > 0.5 else "yellow",
                "detail": f"{cex_value_pct:.0%} of total value sits in CEX wallets",
                "recommendation": "CEX wallets aggregate many users behind one address. Consider filtering them for accurate user metrics.",
            })

    # 2. Sybil cohort: >20% of wallets flagged
    if 'sybil_risk_score' in df.columns:
        sybil_count = len(df[df['sybil_risk_score'] >= 40])
        sybil_pct = sybil_count / total
        if sybil_pct > 0.2:
            flags.append({
                "flag": "sybil_cohort",
                "severity": "red" if sybil_pct > 0.4 else "yellow",
                "detail": f"{sybil_count} wallets ({sybil_pct:.0%}) show sybil/farming patterns",
                "recommendation": "Implement sybil filtering before airdrops or reward distributions to protect budgets.",
            })

    # 3. Whale concentration: top 5 wallets hold >50% of value
    if total_usd > 0 and total >= 5:
        top5_usd = df.nlargest(5, 'est_net_worth_usd')['est_net_worth_usd'].sum()
        top5_pct = top5_usd / total_usd
        if top5_pct > 0.5:
            flags.append({
                "flag": "whale_concentration",
                "severity": "red" if top5_pct > 0.8 else "yellow",
                "detail": f"Top 5 wallets control {top5_pct:.0%} of total value",
                "recommendation": "High concentration increases risk from individual wallet movements. Diversify holder base.",
            })

    # 4. Low user ratio: <50% real users
    user_count = len(df[df['wallet_type'] == 'USER'])
    user_pct = user_count / total
    if user_pct < 0.5:
        flags.append({
            "flag": "low_user_ratio",
            "severity": "red" if user_pct < 0.3 else "yellow",
            "detail": f"Only {user_pct:.0%} of wallets are real end-users",
            "recommendation": "High infrastructure ratio may indicate bot activity or data quality issues. Review wallet classification.",
        })

    # 5. Low activity: average tx_count < 10
    if 'tx_count' in df.columns:
        avg_tx = df['tx_count'].mean()
        if avg_tx < 10:
            flags.append({
                "flag": "low_activity",
                "severity": "yellow",
                "detail": f"Average transaction count is {avg_tx:.1f}",
                "recommendation": "Low activity suggests passive holders or dust wallets. Consider activation campaigns.",
            })

    # 6. Sanctions presence
    if 'sanctions_hit' in df.columns:
        sanctions_count = len(df[df['sanctions_hit'] == True])
        if sanctions_count > 0:
            flags.append({
                "flag": "sanctions_presence",
                "severity": "red",
                "detail": f"{sanctions_count} wallet(s) matched international sanctions lists",
                "recommendation": "Immediate compliance review required. Consider blocking sanctioned addresses.",
            })

    # Add green flags if nothing bad found
    if not flags:
        flags.append({
            "flag": "healthy",
            "severity": "green",
            "detail": "No significant risk flags detected",
            "recommendation": "Community appears healthy. Continue monitoring with periodic re-analysis.",
        })

    return flags


def compute_concentration_metrics(df) -> dict:
    """
    Compute value distribution concentration metrics.
    """
    total = len(df)
    if total == 0:
        return {"gini": 0, "top_1pct_share": 0, "top_5pct_share": 0, "top_10pct_share": 0, "hhi": 0}

    values = df['est_net_worth_usd'].sort_values(ascending=True).values.astype(float)
    total_usd = values.sum()

    # Gini coefficient
    if total_usd > 0 and total > 1:
        index = np.arange(1, total + 1)
        gini = (2 * np.sum(index * values) - (total + 1) * total_usd) / (total * total_usd)
        gini = round(float(max(min(gini, 1.0), 0.0)), 4)
    else:
        gini = 0.0

    # Top-N shares
    sorted_desc = np.sort(values)[::-1]
    def top_pct_share(pct):
        n = max(1, int(math.ceil(total * pct)))
        return round(float(sorted_desc[:n].sum() / total_usd), 4) if total_usd > 0 else 0.0

    top_1 = top_pct_share(0.01)
    top_5 = top_pct_share(0.05)
    top_10 = top_pct_share(0.10)

    # HHI (normalized): sum of squared market shares
    if total_usd > 0:
        shares = values / total_usd
        hhi = round(float(np.sum(shares ** 2)), 6)
    else:
        hhi = 0.0

    return {
        "gini": gini,
        "top_1pct_share": top_1,
        "top_5pct_share": top_5,
        "top_10pct_share": top_10,
        "hhi": hhi,
    }
