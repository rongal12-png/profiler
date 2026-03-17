# {{ project_name }} — Wallet Intelligence Report

**Reference ID:** `{{ reference_id }}`
**Generated On:** `{{ generation_date }}`
**Community Quality Score:** **{{ community_score.score }}** / 100 (Grade **{{ community_score.grade }}**)

---

## 1. Executive Summary — Company View

This report provides a comprehensive intelligence overview of **{{ project_name }}**'s wallet base, covering **{{ total_wallets }}** unique addresses across **{{ chains_scanned }}** chain{{ "s" if chains_scanned > 1 else "" }}{% if is_multi_chain %} ({{ scans_count }} cross-chain scans aggregated){% endif %}. The total estimated value controlled by these wallets is **{{ total_usd_controlled }}**.
{% if is_multi_chain %}
> **Multi-Chain Scan:** Each wallet's holdings were aggregated across all scanned networks. A wallet holding assets on both Ethereum and Base appears as a single entry with combined net worth. The "Chains with Holdings" column in the appendix tables shows which networks each wallet is active on.
{% endif %}

{% if user_count > 0 %}
Of the {{ total_wallets }} wallets analyzed, **{{ user_count }}** ({{ user_pct }}%) are classified as real end-users (EOA wallets not associated with infrastructure). These are the wallets that represent genuine engagement with {{ project_name }}. The remaining **{{ infra_total }}** wallet{{ "s" if infra_total != 1 else "" }} belong to infrastructure: {{ cex_count }} centralized exchange{{ "s" if cex_count != 1 else "" }} (CEX), {{ dex_count }} DEX router{{ "s" if dex_count != 1 else "" }}, {{ bridge_count }} bridge{{ "s" if bridge_count != 1 else "" }}, {{ protocol_count }} protocol/contract address{{ "es" if protocol_count != 1 else "" }}, and {{ contract_count }} unlabeled smart contract{{ "s" if contract_count != 1 else "" }}.
{% else %}
No wallets were classified as real end-users. This may indicate a data set composed entirely of infrastructure addresses, or that additional labeling is needed.
{% endif %}

{% if whale_count > 0 %}
Among real users, **{{ whale_count }}** wallet{{ "s" if whale_count != 1 else "" }} qualified as **Whales** (investor score ≥ 55 or identified VC/KOL), holding a combined **{{ whale_usd }}** and representing the most strategically important segment for partnership and VIP outreach. **{{ tuna_count }}** wallet{{ "s" if tuna_count != 1 else "" }} are **Tuna** — active investors with moderate portfolios who are prime candidates for community programs. The remaining **{{ fish_count }}** are **Fish** — smaller or less-active users who may respond to growth campaigns and incentive programs.
{% else %}
No wallets in this set reached Whale status. The user base is composed of **{{ tuna_count }}** Tuna (moderate investors) and **{{ fish_count }}** Fish (smaller or newer users). This is common for early-stage projects or sets focused on community members rather than institutional participants.
{% endif %}

The average investor quality score across all real users is **{{ avg_investor_score }}** / 100. {{ "This suggests strong investor quality with experienced DeFi participants." if avg_investor_score|float > 40 else "This suggests moderate quality — the base contains a mix of experienced and newer participants." if avg_investor_score|float > 25 else "This suggests an early-stage community with mostly new or small participants — growth efforts should focus on activation and education." }}

| Metric | Value |
|---|---|
| **Total Wallets Analyzed** | {{ total_wallets }}{% if failed_count > 0 %} (⚠ {{ failed_count }} failed — see note below){% endif %} |
| **Real Users** | {{ user_count }} ({{ user_pct }}%) |
| **Infrastructure Wallets** | {{ infra_total }} (CEX: {{ cex_count }}, DEX: {{ dex_count }}, Bridge: {{ bridge_count }}, Protocol: {{ protocol_count }}, Contract: {{ contract_count }}) |
| **Total Estimated USD** | {{ total_usd_controlled }} |
| **Whale / Tuna / Fish** | {{ whale_count }} / {{ tuna_count }} / {{ fish_count }} |
| **Average Investor Score** | {{ avg_investor_score }} |
| **Community Quality Score** | {{ community_score.score }} ({{ community_score.grade }}) |
| **VC/KOL Wallets Identified** | {{ labeled_summary.vc_kol_count }} |
| **Sybil Risk Wallets** | {{ risk_overview.sybil_risk_count }} |
| **Sanctions Hits** | {{ sanctions_count }} |

{% if plots.tier_dist_pie %}
### Wallet Tier Distribution
![Tier Distribution](data:image/png;base64,{{ plots.tier_dist_pie }})
{% endif %}

{% if plots.chain_dist_bar %}
### Chain Distribution
![Chain Distribution](data:image/png;base64,{{ plots.chain_dist_bar }})
{% endif %}

{% if failed_count > 0 %}
> **⚠ Data Notice:** {{ failed_count }} wallet{{ "s" if failed_count != 1 else "" }} could not be scanned due to RPC connection failures and {{ "are" if failed_count != 1 else "is" }} excluded from all analysis. {{ "These wallets are" if failed_count != 1 else "This wallet is" }} listed in the appendix. Re-running the analysis may recover them if the connection issue was transient.
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

| Metric | Value |
|---|---|
| **Gini Coefficient** | {{ "%.3f"|format(concentration_metrics.gini) }} |
| **Top 1% Share** | {{ "%.1f"|format(concentration_metrics.top_1pct_share * 100) }}% |
| **Top 5% Share** | {{ "%.1f"|format(concentration_metrics.top_5pct_share * 100) }}% |
| **Top 10% Share** | {{ "%.1f"|format(concentration_metrics.top_10pct_share * 100) }}% |

---

## 3. Product-Focused Insights

Understanding who your users are — and how they behave — is critical for product decisions. This section breaks down your wallet base by investor quality, persona, and engagement patterns.

### Investor Quality

The multi-component scoring model evaluates each wallet across five dimensions: balance strength, transaction activity, DeFi engagement, reputation signals, and sybil risk. The composite **investor score** weights these factors to produce a single quality metric per wallet.

| Component | Average Score | What It Measures |
|---|---|---|
| **Balance Score** | {{ score_averages.balance_score }} | USD value held (log-scaled) |
| **Activity Score** | {{ score_averages.activity_score }} | Transaction count as engagement proxy |
| **DeFi Investor Score** | {{ score_averages.defi_investor_score }} | Token diversity, stablecoin dry powder, active investing |
| **Reputation Score** | {{ score_averages.reputation_score }} | Known identity (VC/KOL boost, infra penalty) |
| **Sybil Risk Score** | {{ score_averages.sybil_risk_score }} | Bot/farming likelihood (lower is better) |

{% if plots.investor_score_hist %}
![Investor Score Distribution](data:image/png;base64,{{ plots.investor_score_hist }})
{% endif %}

### Persona Segmentation

Each wallet is assigned a primary persona based on behavioral signals. Understanding your persona mix helps tailor product features and communication.

{% for persona, count in persona_distribution.items() %}
- **{{ persona }}**: {{ count }} wallets ({{ "%.1f"|format(count / total_wallets * 100) }}%){% if persona == "Trader" %} — Active market participants who swap and position frequently. Consider advanced trading features and real-time alerts.{% elif persona == "Long-term Holder" %} — Patient capital that holds through cycles. Consider staking programs and governance rights.{% elif persona == "Farmer" %} — Yield-seeking users who move across protocols. Consider competitive APY and composability.{% elif persona == "Airdrop Hunter" %} — High activity with low holdings, potentially farming rewards. Monitor for sybil behavior.{% elif persona == "Infra" %} — Infrastructure wallets (exchanges, routers, bridges). Not end-users.{% elif persona == "Staker" %} — Users with significant staked positions, signaling long-term commitment and governance interest.{% elif persona == "Newcomer" %} — New or small participants with few transactions. Prioritize onboarding and education.{% endif %}
{% endfor %}

{% if plots.persona_dist_pie %}
![Persona Distribution](data:image/png;base64,{{ plots.persona_dist_pie }})
{% endif %}

### Token Intelligence

| Metric | Value |
|---|---|
| **Wallets with Staking Positions** | {{ token_intel.staking_count }} ({{ token_intel.staking_pct }}%) |
| **Wallets with Governance Tokens** | {{ token_intel.governance_count }} ({{ token_intel.governance_pct }}%) |
| **Average Stablecoin Share** | {{ token_intel.avg_stablecoin_share }} |
| **Average Token Diversity** | {{ token_intel.avg_diversity }} tokens |
| **Dry Powder Wallets** | {{ token_intel.dry_powder_count }} |
| **Long-term Signal Wallets** | {{ token_intel.long_term_count }} |

---

## 4. Identity Intelligence

{% if identity_agg.has_data %}
This section provides enriched identity data derived from on-chain signals: ENS names, wallet funding source, NFT holdings, and wallet age. These signals are probabilistic — they indicate likely characteristics, not verified facts.

**Coverage:** {{ identity_agg.enriched_count }} of {{ total_wallets }} wallets enriched ({{ identity_agg.enriched_pct }}%).

{% if identity_agg.funding_breakdown %}
### Funding Source Exchanges

Wallets whose original funding transaction came from a known centralized exchange:

| Exchange | Wallets Funded |
|---|---|
{% for cex, count in identity_agg.funding_breakdown %}
| {{ cex }} | {{ count }} |
{% endfor %}
{% endif %}

{% if identity_agg.ens_count > 0 %}
### ENS Identity (Ethereum)

**{{ identity_agg.ens_count }}** wallets ({{ identity_agg.ens_pct }}%) have a registered ENS name, indicating established on-chain identity and a higher likelihood of being genuine long-term Ethereum participants.

| Wallet | ENS Name | Tier | Net Worth |
|---|---|---|---|
{% for w in identity_agg.ens_wallets %}
| `{{ w.address }}` | **{{ w.ens_name }}** | {{ w.tier }} | ${{ "%.2f"|format(w.est_net_worth_usd) }} |
{% endfor %}
{% endif %}

{% if identity_agg.nft_holder_count > 0 %}
### NFT Portfolio

| Metric | Value |
|---|---|
| **NFT Holders** | {{ identity_agg.nft_holder_count }} ({{ identity_agg.nft_holder_pct }}% of total) |
| **Blue-Chip NFT Holders** | {{ identity_agg.blue_chip_count }} |

{% if identity_agg.blue_chip_breakdown %}
**Blue-chip collections held:**

| Collection | Holders |
|---|---|
{% for col, count in identity_agg.blue_chip_breakdown %}
| {{ col }} | {{ count }} |
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
| {{ bucket.range }} | {{ bucket.count }} |
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
| **High** | {{ intent_agg.readiness.high|default(0) }} | Multiple strong signals — actively deploying capital or positioned to invest |
| **Medium** | {{ intent_agg.readiness.medium|default(0) }} | Some positive signals — engaged but moderate positioning |
| **Low** | {{ intent_agg.readiness.low|default(0) }} | Few signals — passive, new, or small participants |

**Total Estimated Deployable Capital:** ${{ "%.2f"|format(intent_agg.total_deployable_usd) }}
This represents the combined stablecoin and liquid native token holdings across all wallets — capital that could be deployed into new investments.

{% if intent_agg.signal_counts %}
### Signal Frequency

| Signal | Wallets Showing Signal |
|---|---|
{% for signal, count in intent_agg.signal_counts.items() %}
| {{ signal|replace('_', ' ')|title }} | {{ count }} |
{% endfor %}
{% endif %}

---

## 6. Marketing & Growth Actions

This section translates the wallet intelligence into actionable strategies for each user tier.

{% if whale_count > 0 %}
### Whale Strategy ({{ whale_count }} wallets, {{ whale_usd }})

Whales are your highest-value users and often your most influential advocates. These wallets have high investor scores, significant capital, or are identified as VC/KOL entities. A dedicated relationship approach is recommended:

- **Direct outreach**: Personal introductions from the founding team, private Discord/Telegram channels, early access to governance proposals.
- **Co-marketing**: Explore co-investment or endorsement opportunities with identified VCs and KOLs.
- **Retention monitoring**: Set up alerts for large outflows from whale wallets — a departing whale often signals broader sentiment shifts.
{% endif %}

{% if tuna_count > 0 %}
### Tuna Strategy ({{ tuna_count }} wallets)

Tuna represent your engaged middle class — active enough to be valuable, large enough to grow into whales. Focus on:

- **Community programs**: Ambassador roles, early access to new features, referral bonuses.
- **Education**: Guided DeFi strategies, yield optimization tutorials, portfolio tracking tools.
- **Progression incentives**: Tiered rewards that encourage increased engagement and deposits.
{% endif %}

{% if fish_count > 0 %}
### Fish Strategy ({{ fish_count }} wallets)

Fish are your largest segment by count but smallest by value. Many are new to the ecosystem or testing the waters. Growth actions:

- **Activation campaigns**: Low-barrier entry programs, welcome bonuses, simplified onboarding.
- **Social proof**: Showcase whale participation and VC backing to build confidence.
- **Gamification**: Quests, badges, and progressive reward systems to drive habitual usage.
{% endif %}

---

## 7. Risk & Compliance View

A clear understanding of non-user wallets is essential for accurate analytics and risk management. Infrastructure wallets (exchanges, DEX routers, bridges, protocol contracts) must be separated from real users to avoid inflating engagement metrics and misallocating resources.

### Why Infrastructure Wallets Matter

**Centralized Exchanges (CEX):** {{ cex_count }} wallet{{ "s" if cex_count != 1 else "" }} identified. CEX hot wallets aggregate thousands of end-users behind a single address. Including them in user counts dramatically overstates individual engagement. Their large balances can also skew net worth statistics — a single Binance hot wallet may hold more USD value than all retail users combined, but it represents custody infrastructure, not an investor.

**DEX Routers:** {{ dex_count }} wallet{{ "s" if dex_count != 1 else "" }} identified. Router contracts (Uniswap, SushiSwap, 1inch, Jupiter) are intermediaries that execute swaps on behalf of users. They do not hold persistent balances and should never be classified as exchanges or investors. Their transaction counts can be astronomical, which would distort activity metrics if included.

**Bridges:** {{ bridge_count }} wallet{{ "s" if bridge_count != 1 else "" }} identified. Bridge contracts (Hop, Stargate, Across, Wormhole, L2 canonical bridges) facilitate cross-chain transfers. Like routers, they are pass-through infrastructure. Their presence in a wallet set may indicate cross-chain user activity, which is a positive signal — but the bridge contract itself is not a user.

**Protocol Contracts:** {{ protocol_count }} contract{{ "s" if protocol_count != 1 else "" }} identified. These include lending pools, staking contracts, token contracts, and other DeFi primitives. They are integral to on-chain infrastructure but do not represent investor activity.

{% if contract_count > 0 %}
**Unlabeled Contracts:** {{ contract_count }} address{{ "es" if contract_count != 1 else "" }} detected as smart contracts without a known label. These could be custom vaults, multisigs, or unidentified protocols. Manual review is recommended for any holding significant value.
{% endif %}

{% if sanctions_enabled %}
### Sanctions Screening

{% if sanctions_count > 0 %}
**{{ sanctions_count }}** wallet{{ "s" if sanctions_count != 1 else "" }} matched entries on international sanctions lists (OFAC SDN, EU Consolidated, Israel NBCTF). These addresses should be reviewed immediately and may require blocking or reporting depending on your jurisdiction and compliance obligations.

| Address | Chain | Sanctions List | Entity | Net Worth |
|---|---|---|---|---|
{% for w in sanctions_wallets %}
| `{{ w.address }}` | {{ w.chain }} | {{ w.list_name }} | {{ w.entity_name }} | ${{ "%.2f"|format(w.est_net_worth_usd) }} |
{% endfor %}
{% else %}
No wallets in this set matched any entries on the OFAC SDN, EU Consolidated, or Israel NBCTF sanctions lists. This is a positive compliance signal, though periodic re-screening is recommended as sanctions lists are updated regularly.
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
| **CEX Exchange Wallets** | {{ cex_count }} | Custodial aggregators — not individual users |
| **DEX Routers** | {{ dex_count }} | Swap intermediaries — no persistent holdings |
| **Bridges** | {{ bridge_count }} | Cross-chain infrastructure |
| **Protocol Contracts** | {{ protocol_count }} | DeFi primitives, token contracts |
| **Unlabeled Contracts** | {{ contract_count }} | Require manual review |
| **Sybil Risk** | {{ risk_overview.sybil_risk_count }} | Wallets with bot/farming patterns |
| **Sanctions Hits** | {{ sanctions_count }} | Addresses on international sanctions lists |
| **Concentration Risk** | {{ risk_overview.concentration_pct }} | Value held by top Whale wallets |

---

## 8. Data Tables (Appendix)

### Wallet Type Breakdown

| Wallet Type | Count | % of Total | Total Est. USD |
|---|---|---|---|
{% for wt in wallet_type_breakdown %}
| {{ wt.wallet_type }} | {{ wt.count }} | {{ wt.pct }}% | ${{ "%.2f"|format(wt.total_usd) }} |
{% endfor %}

{% if tables.top_by_score %}
### Top 20 Wallets by Investor Score (Users Only)

| Address | Chains with Holdings | Tier | Score | Persona | Net Worth | ENS |
|---|---|---|---|---|---|---|
{% for w in tables.top_by_score %}
| `{{ w.address }}` | {{ w.chains_with_assets or w.get('chain', '-') }} | {{ w.tier }} | {{ w.investor_score }} | {{ w.persona }} | ${{ "%.2f"|format(w.est_net_worth_usd) }} | {{ w.ens_name or '-' }} |
{% endfor %}
{% endif %}

{% if tables.top_whales %}
### Top 20 Wallets by Net Worth

| Address | Chains with Holdings | Tier | Net Worth | Stablecoins | Label | ENS |
|---|---|---|---|---|---|---|
{% for w in tables.top_whales %}
| `{{ w.address }}` | {{ w.chains_with_assets or w.get('chain', '-') }} | {{ w.tier }} | ${{ "%.2f"|format(w.est_net_worth_usd) }} | ${{ "%.2f"|format(w.stable_usd_total) }} | {{ w.labels_str or '-' }} | {{ w.ens_name or '-' }} |
{% endfor %}
{% endif %}

{% if tables.persona_detail %}
### Persona Detail (Top 20 by Confidence)

| Address | Chain | Persona | Confidence | Evidence | Secondary | Net Worth |
|---|---|---|---|---|---|---|
{% for w in tables.persona_detail %}
| `{{ w.address }}` | {{ w.chain }} | {{ w.persona }} | {{ "%.0f"|format(w.confidence * 100) }}% | {{ w.evidence }} | {{ w.secondary }} | ${{ "%.2f"|format(w.est_net_worth_usd) }} |
{% endfor %}
{% endif %}

{% if tables.cex_wallets %}
### CEX Exchange Wallets

| Address | Chain | Label | Est. Value (USD) | Confidence |
|---|---|---|---|---|
{% for w in tables.cex_wallets %}
| `{{ w.address }}` | {{ w.chain }} | {{ w.labels_str }} | ${{ "%.2f"|format(w.est_net_worth_usd) }} | {{ w.confidence }} |
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
| `{{ w.address }}` | {{ w.chain }} | {{ w.labels_str }} | ${{ "%.2f"|format(w.est_net_worth_usd) }} | {{ w.confidence }} |
{% endfor %}
{% endif %}

{% if tables.high_activity_low_balance %}
### High Activity / Low Balance (Potential Sybil)

| Address | Chain | TX Count | Net Worth | Sybil Risk | Wallet Type |
|---|---|---|---|---|---|
{% for a in tables.high_activity_low_balance %}
| `{{ a.address }}` | {{ a.chain }} | {{ a.tx_count }} | ${{ "%.2f"|format(a.est_net_worth_usd) }} | {{ a.sybil_risk_score }} | {{ a.wallet_type }} |
{% endfor %}
{% endif %}

{% if failed_count > 0 %}
### Failed Scans ({{ failed_count }} wallet{{ "s" if failed_count != 1 else "" }})

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
| {{ c.chain }} | {{ c.count }} | ${{ "%.2f"|format(c.sum) }} | {{ "%.1f"|format(c.avg_score) }} |
{% endfor %}

### Wealth Distribution (Users Only)

| Bucket | Count | Total USD |
|---|---|---|
{% for bucket in wealth_buckets %}
| {{ bucket.range }} | {{ bucket.count }} | ${{ "%.2f"|format(bucket.total_usd) }} |
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
| `{{ w.address }}` | {{ w.chain }} | {{ w.label_name }} | {{ w.label_type }} | ${{ "%.2f"|format(w.est_net_worth_usd) }} | {{ w.investor_score }} |
{% endfor %}

**Summary:** {{ labeled_summary.vc_kol_count }} VC/KOL wallets controlling {{ labeled_summary.vc_kol_usd }} total.
{% endif %}

---

## 9. Recommendations

Based on this analysis, the following actions are recommended for {{ project_name }}:

{% if whale_count > 0 %}
**Whale Retention & Engagement.** {{ whale_count }} whale wallet{{ "s" if whale_count != 1 else "" }} control{{ "s" if whale_count == 1 else "" }} a disproportionate share of value ({{ risk_overview.concentration_pct }} concentration). Establish direct communication channels with these holders. Set up automated monitoring for large outflows — losing even one whale can significantly impact TVL and market perception. Consider a dedicated account manager or VIP program.
{% endif %}

{% if labeled_summary.vc_kol_count > 0 %}
**Leverage VC/KOL Presence.** {{ labeled_summary.vc_kol_count }} identified VC or KOL wallet{{ "s" if labeled_summary.vc_kol_count != 1 else "" }} provide{{ "s" if labeled_summary.vc_kol_count == 1 else "" }} strong social proof. Coordinate with these entities for co-marketing, endorsements, and strategic partnerships. Their on-chain activity validates {{ project_name }}'s credibility.
{% endif %}

{% if risk_overview.sybil_risk_count > 0 %}
**Sybil Mitigation.** {{ risk_overview.sybil_risk_count }} wallet{{ "s" if risk_overview.sybil_risk_count != 1 else "" }} flagged for sybil/farming behavior. Before any airdrop or reward distribution, implement additional verification (minimum balance requirements, time-weighted participation, or identity attestation). This protects reward budgets and ensures genuine users benefit.
{% endif %}

{% if cex_count > 0 %}
**Exchange Monitoring.** {{ cex_count }} CEX wallet{{ "s" if cex_count != 1 else "" }} detected. Monitor inflows/outflows to these addresses as they may signal upcoming selling pressure or new buying interest. CEX deposit spikes often precede price movements.
{% endif %}

{% if token_intel.staking_count > 0 %}
**Staking Community.** {{ token_intel.staking_count }} wallets hold staked assets, indicating long-term commitment. Consider expanding staking rewards, governance participation incentives, and validator delegation programs to retain these engaged users.
{% endif %}

{% if intent_agg.readiness.high|default(0) > 0 %}
**High-Readiness Investors.** {{ intent_agg.readiness.high }} wallets show high investment readiness with ${{ "%.0f"|format(intent_agg.total_deployable_usd) }} in estimated deployable capital. Time-sensitive opportunities (IDOs, early access, limited allocations) should target this segment first.
{% endif %}

**Data Quality.** Invest in expanding the known labels database for {{ project_name }}'s specific ecosystem. More labels lead to more accurate user/infra separation and better analytics. Consider integrating with third-party labeling services (Arkham, Nansen) for enriched intelligence.

**Next Analysis.** Re-run this analysis periodically (weekly or monthly) to track user base evolution, whale retention, and sybil trends. Comparing reports over time reveals growth trajectory and community health.
