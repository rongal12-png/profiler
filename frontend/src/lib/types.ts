export type JobStatus = "PENDING" | "IN_PROGRESS" | "PAUSED" | "STOPPED" | "COMPLETED" | "FAILED";

export interface SubmitJobResponse {
  job_id: number;
  message: string;
}

export type ReportFormat = "json" | "csv" | "markdown" | "html" | "pdf" | "docx";

// --- Wallet-level data (per-wallet record from JSON report) ---

export interface TokenIntelligence {
  categories: Record<string, { usd: number; pct: number; tokens?: string[] }>;
  total_usd: number;
  concentration: number;
  stablecoin_share: number;
  staked_share: number;
  token_diversity: number;
  has_staking_positions: boolean;
  has_governance_tokens: boolean;
  dry_powder_signal: boolean;
  long_term_signal: boolean;
}

export interface PersonaDetail {
  primary: string;
  confidence: number;
  evidence: string[];
  secondary: string | null;
}

export interface IntentSignal {
  signal: string;
  strength: "strong" | "moderate" | "weak";
  detail: string;
}

export interface IntentSignals {
  signals: IntentSignal[];
  investment_readiness: "high" | "medium" | "low";
  estimated_deployable_usd: number;
}

export interface WalletRecord {
  address: string;
  chain: string;           // primary chain (highest USD value)
  scan_chains: string;     // all chains scanned, comma-separated (e.g. "arbitrum, ethereum")
  chains_with_assets: string; // chains where wallet has actual holdings
  tier: string;
  wallet_type: string;
  investor_score: number;
  persona: string;
  est_net_worth_usd: number;
  stable_usd_total: number;
  native_balance: number;
  balance_score: number;
  activity_score: number;
  defi_investor_score: number;
  reputation_score: number;
  sybil_risk_score: number;
  product_relevance_score: number;
  tx_count: number;
  is_contract: string;
  known_entity_type: string | null;
  labels_str: string;
  risk_flags_str: string;
  confidence: number;
  notes: string | null;
  sanctions_hit: boolean;
  sanctions_list_name: string | null;
  sanctions_entity_name: string | null;
  token_intelligence: TokenIntelligence | null;
  persona_detail: PersonaDetail | null;
  intent_signals: IntentSignals | null;
}

// --- Project-level aggregates ---

export interface CommunityScoreComponent {
  score: number;
  weight: number;
  detail: string;
}

export interface CommunityScore {
  score: number;
  grade: string;
  components: Record<string, CommunityScoreComponent>;
  narrative: string;
}

export interface HealthFlag {
  flag: string;
  severity: "red" | "yellow" | "green";
  detail: string;
  recommendation: string;
}

export interface ConcentrationMetrics {
  gini: number;
  top_1pct_share: number;
  top_5pct_share: number;
  top_10pct_share: number;
  hhi: number;
}

export interface ProjectAggregates {
  community_score: CommunityScore;
  health_flags: HealthFlag[];
  concentration_metrics: ConcentrationMetrics;
  token_intelligence: Record<string, number | string>;
  intent_signals: Record<string, number | string | Record<string, number>>;
  tier_distribution: Record<string, number>;
  persona_distribution: Record<string, number>;
  chain_distribution: Record<string, number>;
  wallet_type_distribution: Record<string, number>;
}

export interface ProjectReport {
  project_name: string;
  job_id: number;
  reference_id: string;
  total_wallets: number;
  wallets: WalletRecord[];
  aggregates: ProjectAggregates;
}

export interface JobStatusResponse {
  job_id: number;
  status: JobStatus;
  total_wallets: number;
  wallets_processed: number;
  project_name: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  elapsed_seconds: number | null;
  result: string | null;
}

// --- Admin types ---

export interface SanctionsListStatus {
  list_name: string;
  status: string;
  record_count: number;
  last_updated: string | null;
  source_url: string;
}

export interface SettingsData {
  scope: string;
  scope_key: string | null;
  settings: {
    scoring: {
      weights: Record<string, number>;
      tier_thresholds: { whale: number; tuna: number };
    };
    sanctions: {
      enabled: boolean;
      lists: Record<string, boolean>;
      action_on_hit: string;
      auto_update_hours: number;
    };
    intelligence: {
      token_categories_enabled: boolean;
      intent_signals_enabled: boolean;
      community_score_enabled: boolean;
      health_flags_enabled: boolean;
    };
    report: {
      sections: Record<string, boolean>;
    };
    operational: {
      max_wallets_per_job: number;
      rpc_timeout_seconds: number;
      retry_count: number;
    };
  };
}

export interface SettingsHistoryEntry {
  id: number;
  scope: string;
  scope_key: string | null;
  version: number;
  is_active: boolean;
  created_by: string;
  created_at: string;
  notes: string | null;
  settings_json: Record<string, unknown>;
}

// --- Project workspace ---

export interface ProjectSummary {
  id: number;
  name: string;
  description: string | null;
  wallet_count: number;
  created_at: string;
  run_count: number;
  last_run_at: string | null;
  last_status: JobStatus | null;
}

export interface ProjectRun {
  job_id: number;
  status: JobStatus;
  total_wallets: number;
  wallets_processed: number;
  created_at: string | null;
  completed_at: string | null;
  elapsed_seconds: number | null;
  result: string | null;
}

export interface ProjectDetail {
  id: number;
  name: string;
  description: string | null;
  wallet_count: number;
  created_at: string;
  runs: ProjectRun[];
}

// --- Recent job (localStorage) ---

export interface RecentJob {
  id: number;
  projectName: string;
  status: JobStatus;
  createdAt: string;
  walletCount: number;
}
