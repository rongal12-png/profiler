# {{ project_name }} — Wallet Intelligence Report

**Reference ID:** `{{ reference_id }}`
**Generated On:** `{{ generation_date }}`
**Community Quality Score:** **{{ community_score.score }}** / 100 (Grade **{{ community_score.grade }}**)

---

## 1. Executive Summary — Company View

This report provides a comprehensive intelligence overview of **{{ project_name }}**'s wallet base, covering **{{ total_wallets | fmt_int }}** unique addresses across **{{ chains_scanned }}** chain{{ "s" if chains_scanned > 1 else "" }}{% if is_multi_chain %} ({{ scans_count | fmt_int }} cross-chain scans aggregated){% endif %}. The total estimated value controlled by these wallets is **{{ total_usd_controlled or "not available" }}**.
{% if is_multi_chain %}
> **Multi-Chain Scan:** Each wallet's holdings were aggregated across all scanned networks. A wallet holding assets on both Ethereum and Base appears as a single entry with combined net worth. The "Chains with Holdings" column in the appendix tables shows which networks each wallet is active on.
{% endif %}

{% if user_count > 0 %}
Of the {{ analyzed_count | fmt_int }} wallets included in this report, **{{ user_count | fmt_int }}** ({{ user_pct }}%) are classified as real end-users (EOA wallets not associated with infrastructure). These are the wallets that represent genuine engagement with {{ project_name }}. The remaining **{{ infra_total | fmt_int }}** wallet{{ "s" if infra_total != 1 else "" }} belong to infrastructure: {{ cex_count | fmt_int }} centralized exchange{{ "s" if cex_count != 1 else "" }} (CEX), {{ dex_count | fmt_int }} DEX router{{ "s" if dex_count != 1 else "" }}, {{ bridge_count | fmt_int }} bridge{{ "s" if bridge_count != 1 else "" }}, {{ protocol_count | fmt_int }} protocol/contract address{{ "es" if protocol_count != 1 else "" }}, and {{ contract_count | fmt_int }} unlabeled smart contract{{ "s" if contract_count != 1 else "" }}.
{% else %}
No wallets were classified as real end-users. This may indicate a data set composed entirely of infrastructure addresses, or that additional labeling is needed.
{% endif %}

{% if whale_count > 0 %}
Among real users, **{{ whale_count | fmt_int }}** wallet{{ "s" if whale_count != 1 else "" }} qualified as **Whales** (capital ≥ $1M, or investor score ≥ 55, or identified VC/KOL), holding a combined **{{ whale_usd or "$0.00" }}**. **{{ tuna_count | fmt_int }}** wallet{{ "s" if tuna_count != 1 else "" }} are **Tuna** — wallets with $10K–$1M in assets or moderate investor scores. The remaining **{{ fish_count | fmt_int }}** are **Fish** — smaller participants, newer wallets, or limited on-chain footprint. In pre-launch or waitlist datasets, a high Fish count is expected and does not imply low community quality.
{% else %}
No wallets in this set reached Whale status. The user base is composed of **{{ tuna_count | fmt_int }}** Tuna (moderate investors) and **{{ fish_count | fmt_int }}** Fish (smaller or newer users). This is common for early-stage projects or sets focused on community members rather than institutional participants.
{% endif %}

{% set _avg_score = avg_investor_score|float %}
The average investor quality score across all real users is **{{ avg_investor_score if avg_investor_score != "nan" else "N/A" }}**{% if avg_investor_score != "nan" %} / 100{% endif %}. {% if _avg_score > 40 %}This suggests strong investor quality with experienced DeFi participants.{% elif _avg_score > 25 %}This suggests moderate quality — the base contains a mix of experienced and newer participants.{% elif user_count > 0 %}This suggests an early-stage community with mostly new or small participants — growth efforts should focus on activation and education.{% else %}Insufficient user data to determine average quality.{% endif %}

| Metric | Value |
|---|---|
| **Total Wallets Analyzed** | {{ total_wallets | fmt_int }}{% if failed_count > 0 %} (⚠ {{ failed_count | fmt_int }} failed — see note below){% endif %} |
| **Real Users** | {{ user_count | fmt_int }} ({{ user_pct }}%) |
| **Infrastructure Wallets** | {{ infra_total | fmt_int }} (CEX: {{ cex_count | fmt_int }}, DEX: {{ dex_count | fmt_int }}, Bridge: {{ bridge_count | fmt_int }}, Protocol: {{ protocol_count | fmt_int }}, Contract: {{ contract_count | fmt_int }}) |
| **Total Estimated USD** | {{ total_usd_controlled or "Not available" }} *(on-chain balances only; excludes off-chain assets)* |
| **Whale / Tuna / Fish** | {{ whale_count | fmt_int }} / {{ tuna_count | fmt_int }} / {{ fish_count | fmt_int }} |
| **Average Investor Score** | {{ avg_investor_score }} |
| **Community Quality Score** | {{ community_score.score }} ({{ community_score.grade }}) |
| **VC/KOL Wallets Identified** | {{ labeled_summary.vc_kol_count | fmt_int }} |
| **Sybil Suspicion** | {{ risk_overview.sybil_flagged_count | fmt_int }} flagged (score ≥ 50) + {{ risk_overview.sybil_suspect_count | fmt_int }} suspect (score 30–49) |
| **Sanctions Hits** | {{ sanctions_count | fmt_int }} |

{% if plots.tier_dist_pie %}
### Wallet Tier Distribution
![Tier Distribution](data:image/png;base64,{{ plots.tier_dist_pie }})
{% endif %}

{% if plots.chain_dist_bar %}
### Chain Distribution
![Chain Distribution](data:image/png;base64,{{ plots.chain_dist_bar }})
{% endif %}

{% if failed_count > 0 %}
> **⚠ Data Notice:** {{ failed_count | fmt_int }} wallet{{ "s" if failed_count != 1 else "" }} could not be scanned due to RPC connection failures and {{ "are" if failed_count != 1 else "is" }} excluded from all analysis. {{ "These wallets are" if failed_count != 1 else "This wallet is" }} listed in the appendix. Re-running the analysis may recover them if the connection issue was transient.
{% endif %}

---

## 2. Community Quality Score

{{ community_score.narrative }}

### Score Breakdown

| Component | Score | Weight | Detail |
|---|---|---|---|
{% for name, comp in community_score.components.items() %}
| **{{ name|replace('_', ' ')|title }}** | {{ comp.score }} | {{ "%.0f"|format(comp.weight * 100) }}% | {{ comp.detail }} |
{% endfor %}
| **Overall** | **{{ community_score.score }}** | 100% | **Grade {{ community_score.grade }}** |

{% if health_flags %}
### Project Health Flags

{% for flag in health_flags %}
- {% if flag.severity == "red" %}**[RED]**{% elif flag.severity == "yellow" %}**[YELLOW]**{% else %}**[GREEN]**{% endif %} **{{ flag.flag|replace('_', ' ')|title }}**: {{ flag.detail }}. *{{ flag.recommendation }}*
{% endfor %}
{% endif %}

### Value Concentration

All concentration figures are computed from the same source ({{ metrics.analyzed_wallets }} analyzed wallets, ordered by USD value).

| Metric | Value | Interpretation |
|---|---|---|
| **Gini Coefficient** | {{ "%.3f"|format(metrics.gini) }} | 0 = perfectly equal, 1 = one wallet holds everything |
| **Largest Single Wallet** | {{ "%.1f"|format(metrics.top1_wallet_share * 100) }}% | Share held by the single highest-value wallet |
| **Top 5 Wallets** | {{ "%.1f"|format(metrics.top5_wallets_share * 100) }}% | Combined share of 5 largest wallets |
| **Top 10 Wallets** | {{ "%.1f"|format(metrics.top10_wallets_share * 100) }}% | Combined share of 10 largest wallets |
| **Top 1% of Wallets** | {{ "%.1f"|format(metrics.top1pct_share * 100) }}% | Share held by top 1% by count (~{{ (metrics.analyzed_wallets * 0.01) | round | int }} wallets) |
| **Top 5% of Wallets** | {{ "%.1f"|format(metrics.top5pct_share * 100) }}% | Share held by top 5% by count |

---

## 3. Product-Focused Insights

Understanding who your users are — and how they behave — is critical for product decisions. This section breaks down your wallet base by investor quality, persona, and engagement patterns.

### Investor Quality

The multi-component scoring model evaluates each wallet across five dimensions: balance strength, transaction activity, DeFi engagement, reputation signals, and sybil risk. The composite **investor score** weights these factors to produce a single quality metric per wallet (0–100 scale).

> **Data sources:** Estimated net worth = native token balance (USD) + ERC-20 stablecoin balances, capped at $1B per wallet to filter decimal errors. Activity is derived from on-chain transaction count. DeFi score reflects token diversity and stablecoin allocation. Scores marked *N/A* indicate wallets with insufficient on-chain data at scan time.

| Component | Average Score | What It Measures |
|---|---|---|
| **Balance Score** | {{ score_averages.balance_score or "N/A" }} | USD value held (log-scaled) |
| **Activity Score** | {{ score_averages.activity_score or "N/A" }} | Transaction count as engagement proxy |
| **DeFi Investor Score** | {{ score_averages.defi_investor_score or "N/A" }} | Token diversity, stablecoin dry powder, active investing |
| **Reputation Score** | {{ score_averages.reputation_score or "N/A" }} | Known identity (VC/KOL boost, infra penalty) |
| **Sybil Risk Score** | {{ score_averages.sybil_risk_score or "N/A" }} | Bot/farming likelihood (lower is better) |

{% if plots.investor_score_hist %}
![Investor Score Distribution](data:image/png;base64,{{ plots.investor_score_hist }})
{% endif %}

### Persona Segmentation

Each wallet is assigned a primary persona based on behavioral signals. Understanding your persona mix helps tailor product features and communication.

{% for persona, count in persona_distribution.items() %}
- **{{ persona }}**: {{ count | fmt_int }} wallet{{ "s" if count != 1 else "" }} ({{ "%.1f"|format(count / persona_denominator * 100) if persona_denominator > 0 else "0.0" }}% of {{ persona_denominator | fmt_int }} analyzed wallets){% if persona == "Trader" %} — Active market participants who swap and position frequently. Consider advanced trading features and real-time alerts.{% elif persona == "Long-term Holder" %} — Patient capital that holds through cycles. Consider staking programs and governance rights.{% elif persona == "Farmer" %} — Yield-seeking users who move across protocols. Consider competitive APY and composability.{% elif persona == "Airdrop Hunter" %} — High activity with low holdings, potentially farming rewards. Monitor for sybil behavior.{% elif persona == "Infra" %} — Infrastructure wallets (exchanges, routers, bridges). Not end-users.{% elif persona == "Staker" %} — Users with significant staked positions, signaling long-term commitment and governance interest.{% elif persona == "Newcomer" %} — New or small participants with few transactions. Prioritize onboarding and education.{% endif %}
{% endfor %}

{% if plots.persona_dist_pie %}
![Persona Distribution](data:image/png;base64,{{ plots.persona_dist_pie }})
{% endif %}

### Token Intelligence

| Metric | Value |
|---|---|
| **Wallets with Staking Positions** | {{ token_intel.staking_count | fmt_int }} ({{ token_intel.staking_pct }}%) |
| **Wallets with Governance Tokens** | {{ token_intel.governance_count | fmt_int }} ({{ token_intel.governance_pct }}%) |
| **Average Stablecoin Share** | {{ token_intel.avg_stablecoin_share }} |
| **Average Token Diversity** | {{ token_intel.avg_diversity }} tokens |
| **Dry Powder Wallets** | {{ token_intel.dry_powder_count | fmt_int }} |
| **Long-term Signal Wallets** | {{ token_intel.long_term_count | fmt_int }} |

---

## 4. Identity Intelligence

{% if identity_agg.has_data %}
This section provides enriched identity data derived from on-chain signals: ENS names, wallet funding source, NFT holdings, and wallet age. These signals are probabilistic — they indicate likely characteristics, not verified facts.

**Coverage:** {{ identity_agg.enriched_count }} of {{ total_wallets | fmt_int }} wallets enriched ({{ identity_agg.enriched_pct }}%).

{% if identity_agg.funding_breakdown %}
### Funding Source Exchanges

Wallets whose original funding transaction came from a known centralized exchange:

| Exchange | Wallets Funded |
|---|---|
{% for cex, count in identity_agg.funding_breakdown %}
| {{ cex }} | {{ count | fmt_int }} |
{% endfor %}
{% endif %}

{% if identity_agg.ens_count > 0 %}
### ENS Identity (Ethereum)

**{{ identity_agg.ens_count | fmt_int }}** wallets ({{ identity_agg.ens_pct }}%) have a registered ENS name, indicating established on-chain identity and a higher likelihood of being genuine long-term Ethereum participants.

| Wallet | ENS Name | Tier | Net Worth |
|---|---|---|---|
{% for w in identity_agg.ens_wallets %}
| `{{ w.address }}` | **{{ w.ens_name }}** | {{ w.tier }} | {{ w.est_net_worth_usd | fmt_usd }} |
{% endfor %}
{% endif %}

{% if identity_agg.nft_holder_count > 0 %}
### NFT Portfolio

| Metric | Value |
|---|---|
| **NFT Holders** | {{ identity_agg.nft_holder_count | fmt_int }} ({{ identity_agg.nft_holder_pct }}% of total) |
| **Blue-Chip NFT Holders** | {{ identity_agg.blue_chip_count | fmt_int }} |

{% if identity_agg.blue_chip_breakdown %}
**Blue-chip collections held:**

| Collection | Holders |
|---|---|
{% for col, count in identity_agg.blue_chip_breakdown %}
| {{ col }} | {{ count | fmt_int }} |
{% endfor %}
{% endif %}

Blue-chip NFT holders (BAYC, CryptoPunks, MAYC, etc.) are typically high-net-worth, culturally engaged Web3 participants with long time horizons. They make excellent targets for premium community programs, exclusive access, and governance participation.
{% endif %}

{% if identity_agg.age_buckets %}
### Wallet Age Distribution

Older wallets (3+ years) represent seasoned on-chain participants who have been active since DeFi Summer or earlier. Newer wallets may indicate recent entrants brought in by the current cycle.

| Age Range | Wallets |
|---|---|
{% for bucket in identity_agg.age_buckets %}
| {{ bucket.range }} | {{ bucket.count | fmt_int }} |
{% endfor %}

{% if identity_agg.avg_wallet_age_days %}
**Average wallet age:** {{ identity_agg.avg_wallet_age_days }} days (~{{ (identity_agg.avg_wallet_age_days / 365) | round(1) }} years).
{% endif %}
{% endif %}

{% else %}
*Identity enrichment data is not available for this report. This feature requires Alchemy RPC endpoints to retrieve funding source history, NFT data, and wallet age. ENS resolution requires an Ethereum RPC.*
{% endif %}

---

## 5. Investment Intelligence

This section analyzes investment readiness and intent signals across the wallet base.

### Investment Readiness Distribution

| Readiness | Count | Description |
|---|---|---|
| **High** | {{ intent_agg.readiness.high|default(0) | fmt_int }} | Multiple strong signals — actively deploying capital or positioned to invest |
| **Medium** | {{ intent_agg.readiness.medium|default(0) | fmt_int }} | Some positive signals — engaged but moderate positioning |
| **Low** | {{ intent_agg.readiness.low|default(0) | fmt_int }} | Few signals — passive, new, or small participants |

**Total Estimated Deployable Capital (Stablecoins):** {{ metrics.deployable_stablecoin_usd | fmt_usd }}
> _Deployable capital = stablecoin holdings only (USDC, USDT, DAI, etc.). Native tokens and non-stable assets are **excluded** — they require a swap step before deployment. Total portfolio value ({{ metrics.total_usd | fmt_usd }}) includes all assets; deployable capital is the ready-to-invest subset._

{% if intent_agg.signal_counts %}
### Signal Frequency

| Signal | Wallets Showing Signal |
|---|---|
{% for signal, count in intent_agg.signal_counts.items() %}
| {{ signal|replace('_', ' ')|title }} | {{ count | fmt_int }} |
{% endfor %}
{% endif %}

---

## 6. Marketing & Growth Actions

This section translates the wallet intelligence into actionable strategies for each user tier.

{% if whale_count > 0 %}
### Whale Strategy ({{ whale_count | fmt_int }} wallets, {{ whale_usd }})

Whales are your highest-value users and often your most influential advocates. These wallets have high investor scores, significant capital, or are identified as VC/KOL entities. A dedicated relationship approach is recommended:

- **Direct outreach**: Personal introductions from the founding team, private Discord/Telegram channels, early access to governance proposals.
- **Co-marketing**: Explore co-investment or endorsement opportunities with identified VCs and KOLs.
- **Retention monitoring**: Set up alerts for large outflows from whale wallets — a departing whale often signals broader sentiment shifts.
{% endif %}

{% if tuna_count > 0 %}
### Tuna Strategy ({{ tuna_count | fmt_int }} wallets)

Tuna represent your engaged middle class — active enough to be valuable, large enough to grow into whales. Focus on:

- **Community programs**: Ambassador roles, early access to new features, referral bonuses.
- **Education**: Guided DeFi strategies, yield optimization tutorials, portfolio tracking tools.
- **Progression incentives**: Tiered rewards that encourage increased engagement and deposits.
{% endif %}

{% if fish_count > 0 %}
### Fish Strategy ({{ fish_count | fmt_int }} wallets)

Fish are your largest segment by count but smallest by value. Many are new to the ecosystem or testing the waters. Growth actions:

- **Activation campaigns**: Low-barrier entry programs, welcome bonuses, simplified onboarding.
- **Social proof**: Showcase whale participation and VC backing to build confidence.
- **Gamification**: Quests, badges, and progressive reward systems to drive habitual usage.
{% endif %}

---

## 7. Risk & Compliance View

A clear understanding of non-user wallets is essential for accurate analytics and risk management. Infrastructure wallets (exchanges, DEX routers, bridges, protocol contracts) must be separated from real users to avoid inflating engagement metrics and misallocating resources.

### Why Infrastructure Wallets Matter

**Centralized Exchanges (CEX):** {{ cex_count | fmt_int }} wallet{{ "s" if cex_count != 1 else "" }} in this dataset **are themselves** exchange infrastructure (hot wallets, cold wallets, custody addresses). This is distinct from wallets that were *funded by* an exchange — {% if metrics.exchange_funded_wallets > 0 %}**{{ metrics.exchange_funded_wallets | fmt_int }}** wallets were originally funded by a known CEX (see Identity Intelligence section), but those wallets belong to end-users, not the exchanges.{% else %}no exchange-funded user wallets were detected in the enriched subset.{% endif %} CEX infrastructure wallets aggregate thousands of end-users behind a single address and are excluded from user analytics.

**DEX Routers:** {{ dex_count | fmt_int }} wallet{{ "s" if dex_count != 1 else "" }} identified. Router contracts (Uniswap, SushiSwap, 1inch, Jupiter) are intermediaries that execute swaps on behalf of users. They do not hold persistent balances and should never be classified as exchanges or investors. Their transaction counts can be astronomical, which would distort activity metrics if included.

**Bridges:** {{ bridge_count | fmt_int }} wallet{{ "s" if bridge_count != 1 else "" }} identified. Bridge contracts (Hop, Stargate, Across, Wormhole, L2 canonical bridges) facilitate cross-chain transfers. Like routers, they are pass-through infrastructure. Their presence in a wallet set may indicate cross-chain user activity, which is a positive signal — but the bridge contract itself is not a user.

**Protocol Contracts:** {{ protocol_count | fmt_int }} contract{{ "s" if protocol_count != 1 else "" }} identified. These include lending pools, staking contracts, token contracts, and other DeFi primitives. They are integral to on-chain infrastructure but do not represent investor activity.

{% if contract_count > 0 %}
**Unlabeled Contracts:** {{ contract_count | fmt_int }} address{{ "es" if contract_count != 1 else "" }} detected as smart contracts without a known label. These could be custom vaults, multisigs, or unidentified protocols. Manual review is recommended for any holding significant value.
{% endif %}

{% if sanctions_enabled %}
### Sanctions Screening

> ⚠️ **Experimental Notice:** This sanctions check is automated and experimental. It is provided for preliminary informational purposes only and does **not** constitute a legal compliance opinion or replace a review by a qualified compliance officer, legal counsel, or licensed screening provider. Address matching is based on publicly available list data and may produce false positives or miss matches due to address format variations, list update delays, or incomplete data. **Do not rely solely on this output for regulatory, legal, or operational decisions.**

{% if sanctions_count > 0 %}
**{{ sanctions_count | fmt_int }}** wallet{{ "s" if sanctions_count != 1 else "" }} returned a potential match against entries on international sanctions lists (OFAC SDN, EU Consolidated, Israel NBCTF). Each flagged address should be independently verified by a qualified compliance professional before any action is taken.

| Address | Chain | Sanctions List | Entity | Net Worth |
|---|---|---|---|---|
{% for w in sanctions_wallets %}
| `{{ w.address }}` | {{ w.chain }} | {{ w.list_name or "Unknown" }} | {{ w.entity_name or "Unknown" }} | {{ w.est_net_worth_usd | fmt_usd }} |
{% endfor %}
{% else %}
No wallets in this set returned a match against the OFAC SDN, EU Consolidated, or Israel NBCTF sanctions lists at the time of scanning. This is not a definitive clearance — sanctions lists are updated frequently and this check should be repeated periodically using an authoritative screening service.
{% endif %}
{% endif %}

{% if health_flags %}
### Project Health Flags

| Flag | Severity | Detail | Recommendation |
|---|---|---|---|
{% for flag in health_flags %}
| {{ flag.flag|replace('_', ' ')|title }} | {{ flag.severity|upper }} | {{ flag.detail }} | {{ flag.recommendation }} |
{% endfor %}
{% endif %}

| Signal | Count | Notes |
|---|---|---|
| **CEX Exchange Wallets** | {{ cex_count | fmt_int }} | Custodial aggregators — not individual users |
| **DEX Routers** | {{ dex_count | fmt_int }} | Swap intermediaries — no persistent holdings |
| **Bridges** | {{ bridge_count | fmt_int }} | Cross-chain infrastructure |
| **Protocol Contracts** | {{ protocol_count | fmt_int }} | DeFi primitives, token contracts |
| **Unlabeled Contracts** | {{ contract_count | fmt_int }} | Require manual review |
| **Sybil Risk** | {{ risk_overview.sybil_risk_count | fmt_int }} | Wallets with bot/farming patterns |
| **Sanctions Hits** | {{ sanctions_count | fmt_int }} | Addresses on international sanctions lists |
| **Concentration Risk (Top 10 Wallets)** | {{ risk_overview.concentration_pct }} | Share of total value held by 10 largest wallets by USD |

---

## 8. Methodology & Limitations

> **Note on Data Interpretation:** This report analyzes on-chain behavior at the time of the scan. For pre-launch or early-stage projects, many wallets may show limited on-chain activity not because of low engagement intent, but because the project has not yet launched. Low activity scores in this context reflect the current state of on-chain behavior, not the holders' overall crypto sophistication.

| Limitation | Details |
|---|---|
| **Wallet Tier** | Whale/Tuna/Fish based on investor score (composite of balance, activity, DeFi, reputation) plus capital floors ($1M+ → Whale, $100K+ → Tuna minimum). Score reflects on-chain behavior quality, not just USD holdings. |
| **Deployable Capital** | Stablecoin holdings only (USDC, USDT, DAI, etc.). Native tokens and non-stable assets are excluded — they are deployable but require a swap. |
| **Concentration Risk** | Calculated as % of total value held by top 10 wallets by USD. A single large wallet can dominate this metric. |
| **CEX Wallets** | "0 CEX wallets" means none of the *scanned wallets* are exchange infrastructure. Wallets *funded by* exchanges (Binance, Bybit, etc.) appear in the funding source analysis — this is different. |
| **Sybil Detection** | Flags wallets with low balance and elevated activity. Score ≥ 50 = flagged; score 30-49 = suspect. Early-stage wallets with low balance are not necessarily sybil — context matters. |
| **Token Detection** | Governance token detection requires Alchemy RPC (Ethereum). Wallets below $50 or with fewer than 5 tx are not enriched. |
| **Label Coverage** | Only wallets matching the known-labels database are tagged. Unknown wallets default to USER classification. |
| **Report Sample** | {% if report_is_sample %}This report includes the top {{ analyzed_count | fmt_int }} wallets by investor score out of {{ total_wallets | fmt_int }} total. Statistics (wallet type counts, tiers) reflect all {{ total_wallets | fmt_int }} wallets.{% else %}All {{ total_wallets | fmt_int }} wallets are included in this report.{% endif %} |

---

## 9. Data Tables (Appendix)

### Wallet Type Breakdown

| Wallet Type | Count | % of Total | Total Est. USD |
|---|---|---|---|
{% for wt in wallet_type_breakdown %}
| {{ wt.wallet_type }} | {{ wt.count }} | {{ wt.pct }}% | {{ wt.total_usd | fmt_usd }} |
{% endfor %}

{% if tables.top_by_score %}
### Top 20 Wallets by Investor Score (Users Only)

| Address | Chains with Holdings | Tier | Score | Persona | Net Worth | ENS |
|---|---|---|---|---|---|---|
{% for w in tables.top_by_score %}
| `{{ w.address }}` | {{ w.chains_with_assets or w.get('chain', '-') }} | {{ w.tier }} | {{ w.investor_score }} | {{ w.persona }} | {{ w.est_net_worth_usd | fmt_usd }} | {{ w.ens_name or '-' }} |
{% endfor %}
{% endif %}

{% if tables.top_whales %}
### Top 20 Wallets by Net Worth

| Address | Chains with Holdings | Tier | Net Worth | Stablecoins | Label | ENS |
|---|---|---|---|---|---|---|
{% for w in tables.top_whales %}
| `{{ w.address }}` | {{ w.chains_with_assets or w.get('chain', '-') }} | {{ w.tier }} | {{ w.est_net_worth_usd | fmt_usd }} | {{ w.stable_usd_total | fmt_usd }} | {{ w.labels_str or '-' }} | {{ w.ens_name or '-' }} |
{% endfor %}
{% endif %}

{% if tables.persona_detail %}
### Persona Detail (Top 20 by Confidence)

| Address | Chain | Persona | Confidence | Evidence | Secondary | Net Worth |
|---|---|---|---|---|---|---|
{% for w in tables.persona_detail %}
| `{{ w.address }}` | {{ w.chain }} | {{ w.persona }} | {{ "%.0f"|format(w.confidence * 100) }}% | {{ w.evidence }} | {{ w.secondary }} | {{ w.est_net_worth_usd | fmt_usd }} |
{% endfor %}
{% endif %}

{% if tables.cex_wallets %}
### CEX Exchange Wallets

| Address | Chain | Label | Est. Value (USD) | Confidence |
|---|---|---|---|---|
{% for w in tables.cex_wallets %}
| `{{ w.address }}` | {{ w.chain }} | {{ w.labels_str }} | {{ w.est_net_worth_usd | fmt_usd }} | {{ w.confidence }} |
{% endfor %}
{% endif %}

{% if tables.dex_wallets %}
### DEX Routers

| Address | Chain | Label | Confidence |
|---|---|---|---|
{% for w in tables.dex_wallets %}
| `{{ w.address }}` | {{ w.chain }} | {{ w.labels_str }} | {{ w.confidence }} |
{% endfor %}
{% endif %}

{% if tables.bridge_wallets %}
### Bridges

| Address | Chain | Label | Est. Value (USD) | Confidence |
|---|---|---|---|---|
{% for w in tables.bridge_wallets %}
| `{{ w.address }}` | {{ w.chain }} | {{ w.labels_str }} | {{ w.est_net_worth_usd | fmt_usd }} | {{ w.confidence }} |
{% endfor %}
{% endif %}

{% if tables.high_activity_low_balance %}
### High Activity / Low Balance (Sybil Suspicion)

Wallets shown here have elevated on-chain activity relative to their balance, which matches patterns associated with sybil farming or airdrop hunting. **Score ≥ 50 = flagged; score 30–49 = suspect.** A score of 0 here means the wallet appears in this table due to the tx/balance ratio filter, but did not trigger the automated suspicion model — manual review recommended.

| Address | Chain | TX Count | Net Worth | Suspicion Score | Wallet Type |
|---|---|---|---|---|---|
{% for a in tables.high_activity_low_balance %}
| `{{ a.address }}` | {{ a.chain }} | {{ a.tx_count }} | {{ a.est_net_worth_usd | fmt_usd }} | {{ a.sybil_risk_score }} | {{ a.wallet_type }} |
{% endfor %}
{% endif %}

{% if failed_count > 0 %}
### Failed Scans ({{ failed_count | fmt_int }} wallet{{ "s" if failed_count != 1 else "" }})

The following wallets could not be analyzed due to RPC connection failures. Their data is not included in any counts or statistics above.

| Address | Chain | Reason |
|---|---|---|
{% for w in tables.failed_wallets %}
| `{{ w.address }}` | {{ w.chain }} | {{ w.notes }} |
{% endfor %}
{% endif %}

### Breakdown by Chain

| Chain | Wallet Count | Total Est. Value (USD) | Avg Investor Score |
|---|---|---|---|
{% for c in tables.chain_breakdown %}
| {{ c.chain }} | {{ c.count | fmt_int }} | {{ c.sum | fmt_usd }} | {{ c.avg_score | fmt_num(1) }} |
{% endfor %}

### Wealth Distribution (Users Only)

| Bucket | Count | Total USD |
|---|---|---|
{% for bucket in wealth_buckets %}
| {{ bucket.range }} | {{ bucket.count | fmt_int }} | {{ bucket.total_usd | fmt_usd }} |
{% endfor %}

{% if plots.stable_vs_native_pie %}
### Stablecoin vs Native Holdings
![Stablecoin vs Native](data:image/png;base64,{{ plots.stable_vs_native_pie }})
{% endif %}

{% if labeled_wallets %}
### VC / KOL / Known Entities

| Address | Chain | Label | Type | Net Worth (USD) | Investor Score |
|---|---|---|---|---|---|
{% for w in labeled_wallets %}
| `{{ w.address }}` | {{ w.chain }} | {{ w.label_name }} | {{ w.label_type }} | {{ w.est_net_worth_usd | fmt_usd }} | {{ w.investor_score }} |
{% endfor %}

**Summary:** {{ labeled_summary.vc_kol_count | fmt_int }} VC/KOL wallets controlling {{ labeled_summary.vc_kol_usd }} total.
{% endif %}

---

## 9. Recommendations

Based on this analysis, the following actions are recommended for {{ project_name }}:

{% if whale_count > 0 %}
**Whale Retention & Engagement.** {{ whale_count | fmt_int }} whale wallet{{ "s" if whale_count != 1 else "" }} control{{ "s" if whale_count == 1 else "" }} a disproportionate share of value ({{ risk_overview.concentration_pct }} concentration). Establish direct communication channels with these holders. Set up automated monitoring for large outflows — losing even one whale can significantly impact TVL and market perception. Consider a dedicated account manager or VIP program.
{% endif %}

{% if labeled_summary.vc_kol_count > 0 %}
**Leverage VC/KOL Presence.** {{ labeled_summary.vc_kol_count | fmt_int }} identified VC or KOL wallet{{ "s" if labeled_summary.vc_kol_count != 1 else "" }} provide{{ "s" if labeled_summary.vc_kol_count == 1 else "" }} strong social proof. Coordinate with these entities for co-marketing, endorsements, and strategic partnerships. Their on-chain activity validates {{ project_name }}'s credibility.
{% endif %}

{% if risk_overview.sybil_risk_count > 0 %}
**Sybil Mitigation.** {{ risk_overview.sybil_risk_count | fmt_int }} wallet{{ "s" if risk_overview.sybil_risk_count != 1 else "" }} flagged for sybil/farming behavior. Before any airdrop or reward distribution, implement additional verification (minimum balance requirements, time-weighted participation, or identity attestation). This protects reward budgets and ensures genuine users benefit.
{% endif %}

{% if cex_count > 0 %}
**Exchange Monitoring.** {{ cex_count | fmt_int }} CEX wallet{{ "s" if cex_count != 1 else "" }} detected. Monitor inflows/outflows to these addresses as they may signal upcoming selling pressure or new buying interest. CEX deposit spikes often precede price movements.
{% endif %}

{% if token_intel.staking_count > 0 %}
**Staking Community.** {{ token_intel.staking_count | fmt_int }} wallets hold staked assets, indicating long-term commitment. Consider expanding staking rewards, governance participation incentives, and validator delegation programs to retain these engaged users.
{% endif %}

{% if intent_agg.readiness.high|default(0) > 0 %}
**High-Readiness Investors.** {{ intent_agg.readiness.high }} wallets show high investment readiness with {{ intent_agg.total_deployable_usd | fmt_usd }} in estimated deployable capital. Time-sensitive opportunities (IDOs, early access, limited allocations) should target this segment first.
{% endif %}

**Data Quality.** Invest in expanding the known labels database for {{ project_name }}'s specific ecosystem. More labels lead to more accurate user/infra separation and better analytics. Consider integrating with third-party labeling services (Arkham, Nansen) for enriched intelligence.

**Next Analysis.** Re-run this analysis periodically (weekly or monthly) to track user base evolution, whale retention, and sybil trends. Comparing reports over time reveals growth trajectory and community health.
