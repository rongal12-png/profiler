import type { ProjectReport, WalletRecord } from "@/lib/types";
import { formatUsd, formatPct, truncateAddress } from "@/lib/aggregates";
import Card from "@/components/ui/Card";
import ProgressBar from "@/components/ui/ProgressBar";
import Badge from "@/components/ui/Badge";
import StatCard from "@/components/ui/StatCard";

interface Props {
  report: ProjectReport;
}

export default function IntelligenceTab({ report }: Props) {
  const { aggregates, wallets } = report;
  const ti = aggregates.token_intelligence;
  const is = aggregates.intent_signals;

  // Readiness distribution
  const readinessDist = (is.readiness_distribution || {}) as Record<string, number>;
  const totalReadiness = Object.values(readinessDist).reduce((a: number, b) => a + (b as number), 0);

  // Signal frequency
  const signalFreq = (is.signal_frequency || {}) as Record<string, number>;
  const sortedSignals = Object.entries(signalFreq).sort(([, a], [, b]) => (b as number) - (a as number));

  // Top wallets by persona confidence
  const walletsWithDetail = wallets
    .filter((w: WalletRecord) => w.persona_detail && w.persona_detail.confidence > 0)
    .sort((a, b) => (b.persona_detail?.confidence || 0) - (a.persona_detail?.confidence || 0))
    .slice(0, 20);

  // Concentration
  const cm = aggregates.concentration_metrics;

  return (
    <div className="space-y-6">
      {/* Token Intelligence Aggregate */}
      <Card title="Token Intelligence">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Staking Wallets" value={`${ti.wallets_with_staking || 0}`} sublabel="hold staked assets" />
          <StatCard label="Governance Wallets" value={`${ti.wallets_with_governance || 0}`} sublabel="hold gov tokens" />
          <StatCard label="Avg Stablecoin Share" value={formatPct(Number(ti.avg_stablecoin_share || 0))} />
          <StatCard label="Dry Powder Wallets" value={`${ti.dry_powder_count || 0}`} sublabel="ready to deploy" />
        </div>
      </Card>

      {/* Intent Signals Aggregate */}
      <Card title="Investment Intent Signals">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Readiness Distribution */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Readiness Distribution</h4>
            <div className="space-y-2">
              {["high", "medium", "low"].map((level) => {
                const count = (readinessDist[level] as number) || 0;
                return (
                  <ProgressBar
                    key={level}
                    value={count}
                    max={totalReadiness || 1}
                    label={`${level.charAt(0).toUpperCase() + level.slice(1)} (${count})`}
                    showPct
                    color={level === "high" ? "bg-green-500" : level === "medium" ? "bg-yellow-400" : "bg-gray-300"}
                  />
                );
              })}
            </div>
            <p className="mt-3 text-sm text-gray-600">
              Total deployable capital: <span className="font-semibold">{formatUsd(Number(is.total_deployable_usd || 0))}</span>
            </p>
          </div>

          {/* Signal Frequency */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Signal Frequency</h4>
            <div className="space-y-2">
              {sortedSignals.map(([signal, count]) => (
                <div key={signal} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 capitalize">{signal.replace(/_/g, " ")}</span>
                  <Badge label={String(count)} color="blue" />
                </div>
              ))}
              {sortedSignals.length === 0 && <p className="text-sm text-gray-400">No signals detected</p>}
            </div>
          </div>
        </div>
      </Card>

      {/* Persona Deep Dive */}
      {walletsWithDetail.length > 0 && (
        <Card title="Top Wallets by Persona Confidence">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Address</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Persona</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Confidence</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Evidence</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Secondary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {walletsWithDetail.map((w) => (
                  <tr key={w.address} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-mono text-blue-600">{truncateAddress(w.address)}</td>
                    <td className="px-3 py-2 font-medium text-gray-800">{w.persona_detail!.primary}</td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 rounded-full" style={{ width: `${w.persona_detail!.confidence * 100}%` }} />
                        </div>
                        <span className="text-xs text-gray-400">{(w.persona_detail!.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-3 py-2 text-xs text-gray-500 max-w-xs truncate">
                      {w.persona_detail!.evidence.join("; ")}
                    </td>
                    <td className="px-3 py-2 text-gray-500">{w.persona_detail!.secondary || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Concentration Metrics */}
      <Card title="Value Concentration Metrics">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{cm.gini.toFixed(3)}</p>
            <p className="text-xs text-gray-500 mt-1">Gini Coefficient</p>
            <p className="text-xs text-gray-400">{cm.gini > 0.8 ? "Highly concentrated" : cm.gini > 0.5 ? "Moderate" : "Diversified"}</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{formatPct(cm.top_1pct_share)}</p>
            <p className="text-xs text-gray-500 mt-1">Top 1% Share</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{formatPct(cm.top_5pct_share)}</p>
            <p className="text-xs text-gray-500 mt-1">Top 5% Share</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{formatPct(cm.top_10pct_share)}</p>
            <p className="text-xs text-gray-500 mt-1">Top 10% Share</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{cm.hhi.toFixed(4)}</p>
            <p className="text-xs text-gray-500 mt-1">HHI Index</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
