import type { ProjectReport } from "@/lib/types";
import { formatUsd, formatPct, distributionBars } from "@/lib/aggregates";
import StatCard from "@/components/ui/StatCard";
import GradeRing from "@/components/ui/GradeRing";
import ProgressBar from "@/components/ui/ProgressBar";
import Card from "@/components/ui/Card";

const severityColors: Record<string, string> = {
  red: "border-l-red-500 bg-red-50",
  yellow: "border-l-yellow-400 bg-yellow-50",
  green: "border-l-green-500 bg-green-50",
};

const barColors = ["bg-blue-500", "bg-indigo-500", "bg-cyan-500", "bg-teal-500", "bg-violet-500", "bg-amber-500", "bg-rose-500", "bg-emerald-500"];

interface Props {
  report: ProjectReport;
}

export default function OverviewTab({ report }: Props) {
  const { aggregates, wallets } = report;
  const cs = aggregates.community_score;
  const totalValue = wallets.reduce((s, w) => s + (w.est_net_worth_usd || 0), 0);
  const avgScore = wallets.length > 0
    ? (wallets.reduce((s, w) => s + (w.investor_score || 0), 0) / wallets.length).toFixed(1)
    : "0";
  const sanctioned = wallets.filter((w) => w.sanctions_hit).length;

  return (
    <div className="space-y-6">
      {/* Reference ID */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 font-medium">Reference ID</p>
            <p className="text-lg font-mono font-semibold text-blue-900 mt-1">{report.reference_id}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600 font-medium">Project</p>
            <p className="text-lg font-semibold text-gray-900 mt-1">{report.project_name}</p>
          </div>
        </div>
      </div>

      {/* Stat row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Wallets" value={report.total_wallets.toLocaleString()} />
        <StatCard label="Total Value" value={formatUsd(totalValue)} />
        <StatCard label="Community Grade" value={cs.grade} sublabel={`${cs.score}/100`} />
        <StatCard label="Avg Score" value={avgScore} sublabel={sanctioned > 0 ? `${sanctioned} sanctioned` : undefined} />
      </div>

      {/* Community Quality Score */}
      <Card title="Community Quality Score">
        <div className="flex flex-col md:flex-row gap-6 items-start">
          <GradeRing score={cs.score} grade={cs.grade} size={140} />
          <div className="flex-1 space-y-3">
            {Object.entries(cs.components).map(([key, comp]) => (
              <div key={key}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600 capitalize">{key.replace(/_/g, " ")}</span>
                  <span className="text-gray-500">{comp.score.toFixed(1)} <span className="text-xs text-gray-400">({(comp.weight * 100).toFixed(0)}%)</span></span>
                </div>
                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: `${comp.score}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
        <p className="mt-4 text-sm text-gray-600 leading-relaxed">{cs.narrative}</p>
      </Card>

      {/* Health Flags */}
      {aggregates.health_flags.length > 0 && (
        <Card title="Health Flags">
          <div className="space-y-3">
            {aggregates.health_flags.map((flag, i) => (
              <div
                key={i}
                className={`border-l-4 rounded-lg p-4 ${severityColors[flag.severity] || severityColors.green}`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm text-gray-800 capitalize">
                    {flag.flag.replace(/_/g, " ")}
                  </span>
                  <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                    flag.severity === "red" ? "bg-red-200 text-red-800" : flag.severity === "yellow" ? "bg-yellow-200 text-yellow-800" : "bg-green-200 text-green-800"
                  }`}>
                    {flag.severity}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{flag.detail}</p>
                <p className="text-xs text-gray-500 mt-1">{flag.recommendation}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Distributions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <DistributionCard title="Tier Distribution" dist={aggregates.tier_distribution} />
        <DistributionCard title="Persona Distribution" dist={aggregates.persona_distribution} />
        <DistributionCard title="Chain Distribution" dist={aggregates.chain_distribution} />
      </div>
    </div>
  );
}

function DistributionCard({ title, dist }: { title: string; dist: Record<string, number> }) {
  const bars = distributionBars(dist);
  const total = bars.reduce((s, b) => s + b.count, 0);

  return (
    <Card title={title}>
      <div className="space-y-2.5">
        {bars.map((bar, i) => (
          <div key={bar.label}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-700 font-medium">{bar.label}</span>
              <span className="text-gray-400">{bar.count} ({formatPct(bar.pct)})</span>
            </div>
            <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${barColors[i % barColors.length]}`}
                style={{ width: `${total > 0 ? (bar.count / total) * 100 : 0}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
