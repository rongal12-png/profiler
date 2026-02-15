"use client";

import { useState, useEffect } from "react";
import type { SettingsData } from "@/lib/types";
import Card from "@/components/ui/Card";

interface Props {
  settings: SettingsData;
  onSave: (settingsJson: Record<string, unknown>) => Promise<void>;
}

export default function IntelligenceTab({ settings, onSave }: Props) {
  const intel = settings.settings.intelligence;
  const report = settings.settings.report;
  const ops = settings.settings.operational;

  const [intelligence, setIntelligence] = useState({ ...intel });
  const [sections, setSections] = useState({ ...report.sections });
  const [operational, setOperational] = useState({ ...ops });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    setIntelligence({ ...intel });
    setSections({ ...report.sections });
    setOperational({ ...ops });
  }, [intel, report, ops]);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await onSave({
        intelligence,
        report: { sections },
        operational,
      });
      setMessage({ type: "success", text: "Settings saved!" });
    } catch (e) {
      setMessage({ type: "error", text: e instanceof Error ? e.message : "Save failed" });
    } finally {
      setSaving(false);
    }
  };

  const sectionLabels: Record<string, string> = {
    executive_summary: "Executive Summary",
    community_score_section: "Community Quality Score",
    product_insights: "Product Insights",
    investment_intel_section: "Investment Intelligence",
    marketing: "Marketing & Growth",
    risk_compliance: "Risk & Compliance",
    data_tables: "Data Tables",
    recommendations: "Recommendations",
    sanctions_section: "Sanctions Details",
  };

  return (
    <div className="space-y-6">
      {/* Intelligence Toggles */}
      <Card title="Intelligence Modules">
        <div className="space-y-3">
          {Object.entries(intelligence).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
              <span className="text-sm font-medium text-gray-700 capitalize">{key.replace(/_enabled$/, "").replace(/_/g, " ")}</span>
              <button
                onClick={() => setIntelligence({ ...intelligence, [key]: !value })}
                className={`relative w-11 h-6 rounded-full transition-colors ${value ? "bg-blue-600" : "bg-gray-300"}`}
              >
                <div className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow ${value ? "translate-x-5" : ""}`} />
              </button>
            </div>
          ))}
        </div>
      </Card>

      {/* Report Sections */}
      <Card title="Report Sections">
        <div className="space-y-3">
          {Object.entries(sections).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
              <span className="text-sm font-medium text-gray-700">{sectionLabels[key] || key}</span>
              <button
                onClick={() => setSections({ ...sections, [key]: !value })}
                className={`relative w-11 h-6 rounded-full transition-colors ${value ? "bg-blue-600" : "bg-gray-300"}`}
              >
                <div className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow ${value ? "translate-x-5" : ""}`} />
              </button>
            </div>
          ))}
        </div>
      </Card>

      {/* Operational Settings */}
      <Card title="Operational Settings">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Wallets per Job</label>
            <input
              type="number"
              value={operational.max_wallets_per_job}
              onChange={(e) => setOperational({ ...operational, max_wallets_per_job: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">RPC Timeout (sec)</label>
            <input
              type="number"
              value={operational.rpc_timeout_seconds}
              onChange={(e) => setOperational({ ...operational, rpc_timeout_seconds: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Retry Count</label>
            <input
              type="number"
              value={operational.retry_count}
              onChange={(e) => setOperational({ ...operational, retry_count: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
        </div>
      </Card>

      {message && (
        <div className={`p-3 rounded-lg text-sm ${message.type === "success" ? "bg-green-50 text-green-700 border border-green-200" : "bg-red-50 text-red-700 border border-red-200"}`}>
          {message.text}
        </div>
      )}

      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
        >
          {saving ? "Saving..." : "Save Settings"}
        </button>
      </div>
    </div>
  );
}
