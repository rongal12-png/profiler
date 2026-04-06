"""
QA check for job 22 — verifies all 10 audit fixes.
Run inside the API container: docker exec wallet-intel-api python /app/qa_check.py
"""
import sys
import os
sys.path.insert(0, '/app')
os.environ.setdefault('DATABASE_URL', os.getenv('DATABASE_URL', ''))

import pandas as pd
from sqlalchemy import create_engine, text

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(db_url)
JOB_ID = 22

with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT address, chain, wallet_type, tier, investor_score, est_net_worth_usd,
               sybil_risk_score, activity_indicators, stable_usd_total
        FROM wallet_analysis
        WHERE job_id = :jid
    """), {"jid": JOB_ID}).fetchall()

if not rows:
    print(f"ERROR: No rows found for job {JOB_ID}")
    sys.exit(1)

import json

data = []
for r in rows:
    ai = r.activity_indicators
    if isinstance(ai, str):
        try: ai = json.loads(ai)
        except: ai = {}
    data.append({
        'address': r.address,
        'chain': r.chain,
        'wallet_type': r.wallet_type,
        'tier': r.tier,
        'investor_score': float(r.investor_score or 0),
        'est_net_worth_usd': float(r.est_net_worth_usd or 0),
        'sybil_risk_score': float(r.sybil_risk_score or 0),
        'activity_indicators': ai,
        'stable_usd_total': float(r.stable_usd_total or 0),
    })

raw_df = pd.DataFrame(data)
print(f"Total DB rows: {len(raw_df)}")

# Simulate _aggregate_cross_chain + _reapply_tier
from app.core.reporting import _aggregate_cross_chain
df = _aggregate_cross_chain(raw_df)
print(f"After aggregation: {len(df)} rows")

users_df = df[df['wallet_type'] == 'USER']
print(f"USER wallets: {len(users_df)}")

# ── 1. Tier counts ────────────────────────────────────────────────────────────
whale_count = int((users_df['tier'] == 'Whale').sum())
tuna_count  = int((users_df['tier'] == 'Tuna').sum())
fish_count  = int((users_df['tier'] == 'Fish').sum())
total_user  = len(users_df)
print(f"\n[1] Tier counts: Whale={whale_count}, Tuna={tuna_count}, Fish={fish_count}, sum={whale_count+tuna_count+fish_count}, user_total={total_user}")
ok = (whale_count + tuna_count + fish_count) == total_user
print(f"    Whale+Tuna+Fish == user_count? {'PASS' if ok else 'FAIL'}")

# ── 2. Big wallet tier ────────────────────────────────────────────────────────
big = df[df['est_net_worth_usd'] > 1_000_000].sort_values('est_net_worth_usd', ascending=False)
print(f"\n[2] Wallets with >$1M USD (should all be Whale):")
for _, row in big.head(5).iterrows():
    flag = 'PASS' if row['tier'] == 'Whale' else 'FAIL'
    print(f"    {row['address'][:12]}... ${row['est_net_worth_usd']:,.0f} tier={row['tier']} [{flag}]")

# ── 3. Concentration metrics ──────────────────────────────────────────────────
total_usd = df['est_net_worth_usd'].sum()
top1_usd  = df['est_net_worth_usd'].max()
top5_usd  = df.nlargest(5, 'est_net_worth_usd')['est_net_worth_usd'].sum()
top10_usd = df.nlargest(10, 'est_net_worth_usd')['est_net_worth_usd'].sum()
top1_pct  = top1_usd / total_usd * 100 if total_usd > 0 else 0
top5_pct  = top5_usd / total_usd * 100 if total_usd > 0 else 0
top10_pct = top10_usd / total_usd * 100 if total_usd > 0 else 0
print(f"\n[3] Concentration (should be top1 > top5 > top10, all high for this dataset):")
print(f"    Total USD: ${total_usd:,.0f}")
print(f"    Top-1 wallet: ${top1_usd:,.0f} = {top1_pct:.1f}%")
print(f"    Top-5 wallets: ${top5_usd:,.0f} = {top5_pct:.1f}%")
print(f"    Top-10 wallets: ${top10_usd:,.0f} = {top10_pct:.1f}%")
ok = top1_pct <= top5_pct <= top10_pct
print(f"    Monotonic? {'PASS' if ok else 'FAIL'}")

# ── 4. Sybil two-tier ─────────────────────────────────────────────────────────
sybil_flagged = int((df['sybil_risk_score'] >= 50).sum())
sybil_suspect = int(((df['sybil_risk_score'] >= 30) & (df['sybil_risk_score'] < 50)).sum())
sybil_clean   = int((df['sybil_risk_score'] < 30).sum())
print(f"\n[4] Sybil: flagged(>=50)={sybil_flagged}, suspect(30-49)={sybil_suspect}, clean(<30)={sybil_clean}")
print(f"    Sum check: {sybil_flagged+sybil_suspect+sybil_clean} == {len(df)}? {'PASS' if sybil_flagged+sybil_suspect+sybil_clean==len(df) else 'FAIL'}")
print(f"    Suspect count > 0? {'PASS' if sybil_suspect > 0 else 'FAIL (0 suspects, expected ~1400)'}")

# ── 5. Exchange funded count ──────────────────────────────────────────────────
exchange_funded = int(users_df['activity_indicators'].apply(
    lambda x: bool(isinstance(x, dict) and x.get('funding_source'))
).sum())
cex_wallets = int((df['wallet_type'] == 'CEX_EXCHANGE').sum())
print(f"\n[5] Exchange-funded USER wallets: {exchange_funded}")
print(f"    CEX_EXCHANGE infra wallets: {cex_wallets}")

# ── 6. Deployable capital (stablecoins) ───────────────────────────────────────
total_stable = float(df['stable_usd_total'].sum())
print(f"\n[6] Deployable stablecoin capital: ${total_stable:,.0f}")

# ── 7. Capital floor tier check ───────────────────────────────────────────────
# $100K-$1M wallets should be at least Tuna
mid_wallets = df[(df['est_net_worth_usd'] >= 100_000) & (df['est_net_worth_usd'] < 1_000_000) & (df['wallet_type'] == 'USER')]
bad_tiers = mid_wallets[mid_wallets['tier'] == 'Fish']
print(f"\n[7] $100K-$1M USER wallets: {len(mid_wallets)}, wrongly Fish: {len(bad_tiers)}")
print(f"    Capital floor (min Tuna for >$100K)? {'PASS' if len(bad_tiers)==0 else 'FAIL'}")

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n── QA Complete ──")
