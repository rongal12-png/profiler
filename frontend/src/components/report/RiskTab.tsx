import type { ProjectReport, WalletRecord } from "@/lib/types";
import { truncateAddress, formatUsd } from "@/lib/aggregates";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";

interface Props {
  report: ProjectReport;
}

export default function RiskTab({ report }: Props) {
  const { wallets, aggregates } = report;

  const sanctionedWallets = wallets.filter((w) => w.sanctions_hit);
  const sybilWallets = wallets.filter((w) => w.sybil_risk_score >= 40).sort((a, b) => b.sybil_risk_score - a.sybil_risk_score);

  // Top 5 whales
  const totalUsd = wallets.reduce((s, w) => s + (w.est_net_worth_usd || 0), 0);
  const topWhales = [...wallets].sort((a, b) => b.est_net_worth_usd - a.est_net_worth_usd).slice(0, 5);
  const top5Value = topWhales.reduce((s, w) => s + (w.est_net_worth_usd || 0), 0);
  const top5Pct = totalUsd > 0 ? top5Value / totalUsd : 0;

  return (
    <div className="space-y-6">
      {/* Sanctions */}
      <Card title="Sanctions Screening">
        {sanctionedWallets.length > 0 ? (
          <>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <p className="text-sm font-semibold text-red-800">
                {sanctionedWallets.length} wallet(s) matched international sanctions lists
              </p>
              <p className="text-xs text-red-600 mt-1">Immediate compliance review recommended</p>
            </div>
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Address</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Chain</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Sanctions List</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Entity</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Net Worth</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sanctionedWallets.map((w) => (
                  <tr key={w.address} className="hover:bg-red-50">
                    <td className="px-3 py-2 font-mono text-red-600">{truncateAddress(w.address)}</td>
                    <td className="px-3 py-2 text-gray-600">{w.chain}</td>
                    <td className="px-3 py-2"><Badge label={w.sanctions_list_name || "Unknown"} color="red" /></td>
                    <td className="px-3 py-2 text-gray-600">{w.sanctions_entity_name || "—"}</td>
                    <td className="px-3 py-2 text-gray-700">{formatUsd(w.est_net_worth_usd)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-sm font-semibold text-green-800">No sanctions hits detected</p>
            <p className="text-xs text-green-600 mt-1">All wallets passed sanctions screening</p>
          </div>
        )}
      </Card>

      {/* Sybil Risk */}
      <Card title="Sybil Risk">
        {sybilWallets.length > 0 ? (
          <>
            <p className="text-sm text-gray-600 mb-4">
              <span className="font-semibold">{sybilWallets.length}</span> wallets show sybil/farming patterns (risk score &ge; 40)
            </p>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Address</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Chain</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Sybil Score</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Tx Count</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Net Worth</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {sybilWallets.slice(0, 20).map((w) => (
                    <tr key={w.address} className="hover:bg-yellow-50">
                      <td className="px-3 py-2 font-mono text-gray-700">{truncateAddress(w.address)}</td>
                      <td className="px-3 py-2 text-gray-600">{w.chain}</td>
                      <td className="px-3 py-2">
                        <Badge label={w.sybil_risk_score.toFixed(0)} color={w.sybil_risk_score >= 60 ? "red" : "yellow"} />
                      </td>
                      <td className="px-3 py-2 text-gray-600">{w.tx_count}</td>
                      <td className="px-3 py-2 text-gray-600">{w.wallet_type}</td>
                      <td className="px-3 py-2 text-gray-700">{formatUsd(w.est_net_worth_usd)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-sm font-semibold text-green-800">No sybil wallets detected</p>
          </div>
        )}
      </Card>

      {/* Whale Concentration */}
      <Card title="Whale Concentration">
        <p className="text-sm text-gray-600 mb-4">
          Top 5 wallets control <span className="font-bold">{(top5Pct * 100).toFixed(1)}%</span> ({formatUsd(top5Value)}) of total value
        </p>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Address</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Chain</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Tier</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Net Worth</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">% of Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {topWhales.map((w, i) => (
                <tr key={w.address} className="hover:bg-gray-50">
                  <td className="px-3 py-2 text-gray-400">{i + 1}</td>
                  <td className="px-3 py-2 font-mono text-gray-700">{truncateAddress(w.address)}</td>
                  <td className="px-3 py-2 text-gray-600">{w.chain}</td>
                  <td className="px-3 py-2"><Badge label={w.tier} color={w.tier === "Whale" ? "indigo" : "blue"} /></td>
                  <td className="px-3 py-2 font-medium text-gray-900">{formatUsd(w.est_net_worth_usd)}</td>
                  <td className="px-3 py-2 text-gray-600">{totalUsd > 0 ? ((w.est_net_worth_usd / totalUsd) * 100).toFixed(1) : 0}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Health Flags */}
      {aggregates.health_flags.length > 0 && (
        <Card title="All Health Flags">
          <div className="space-y-3">
            {aggregates.health_flags.map((flag, i) => (
              <div key={i} className={`border-l-4 rounded-lg p-4 ${
                flag.severity === "red" ? "border-l-red-500 bg-red-50" :
                flag.severity === "yellow" ? "border-l-yellow-400 bg-yellow-50" :
                "border-l-green-500 bg-green-50"
              }`}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm text-gray-800 capitalize">{flag.flag.replace(/_/g, " ")}</span>
                  <Badge label={flag.severity} color={flag.severity === "red" ? "red" : flag.severity === "yellow" ? "yellow" : "green"} />
                </div>
                <p className="text-sm text-gray-600">{flag.detail}</p>
                <p className="text-xs text-gray-500 mt-1">{flag.recommendation}</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
