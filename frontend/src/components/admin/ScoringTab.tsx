"use client";

import { useState, useEffect } from "react";
import type { SettingsData } from "@/lib/types";
import Card from "@/components/ui/Card";

interface Props {
  settings: SettingsData;
  onSave: (settingsJson: Record<string, unknown>) => Promise<void>;
}

export default function ScoringTab({ settings, onSave }: Props) {
  const s = settings.settings.scoring;
  const [whale, setWhale] = useState(s.tier_thresholds.whale);
  const [tuna, setTuna] = useState(s.tier_thresholds.tuna);
  const [weights, setWeights] = useState({ ...s.weights });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    setWhale(s.tier_thresholds.whale);
    setTuna(s.tier_thresholds.tuna);
    setWeights({ ...s.weights });
  }, [s]);

  const weightTotal = Object.values(weights).reduce((sum, v) => sum + v, 0);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await onSave({
        scoring: {
          tier_thresholds: { whale, tuna },
          weights,
        },
      });
      setMessage({ type: "success", text: "Scoring settings saved!" });
    } catch (e) {
      setMessage({ type: "error", text: e instanceof Error ? e.message : "Save failed" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Tier Thresholds */}
      <Card title="Tier Thresholds">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Whale Threshold</label>
            <input
              type="number"
              value={whale}
              onChange={(e) => setWhale(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
            <p className="text-xs text-gray-500 mt-1">Score &ge; {whale} = Whale tier</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tuna Threshold</label>
            <input
              type="number"
              value={tuna}
              onChange={(e) => setTuna(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
            <p className="text-xs text-gray-500 mt-1">Score &ge; {tuna} = Tuna tier (below = Fish)</p>
          </div>
        </div>
        {/* Visual scale */}
        <div className="mt-4 relative h-8 bg-gray-100 rounded-full overflow-hidden">
          <div className="absolute inset-y-0 left-0 bg-cyan-200 rounded-l-full" style={{ width: `${tuna}%` }} />
          <div className="absolute inset-y-0 bg-blue-200" style={{ left: `${tuna}%`, width: `${whale - tuna}%` }} />
          <div className="absolute inset-y-0 bg-indigo-300 rounded-r-full" style={{ left: `${whale}%`, width: `${100 - whale}%` }} />
          <div className="absolute inset-0 flex items-center justify-center gap-8 text-xs font-medium">
            <span className="text-cyan-700">Fish &lt;{tuna}</span>
            <span className="text-blue-700">Tuna {tuna}-{whale}</span>
            <span className="text-indigo-700">Whale &ge;{whale}</span>
          </div>
        </div>
      </Card>

      {/* Scoring Weights */}
      <Card title="Scoring Weights">
        <div className="space-y-4">
          {Object.entries(weights).map(([key, value]) => (
            <div key={key} className="flex items-center gap-4">
              <label className="w-28 text-sm font-medium text-gray-700 capitalize">{key}</label>
              <input
                type="number"
                step="0.05"
                value={value}
                onChange={(e) => setWeights({ ...weights, [key]: Number(e.target.value) })}
                className="w-24 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              />
              <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${value >= 0 ? "bg-blue-500" : "bg-red-400"}`}
                  style={{ width: `${Math.abs(value) * 100}%` }}
                />
              </div>
            </div>
          ))}
          <div className="flex items-center justify-between pt-2 border-t">
            <span className="text-sm text-gray-500">Total weight</span>
            <span className={`text-sm font-medium ${Math.abs(weightTotal - 0.8) < 0.01 ? "text-green-600" : "text-amber-600"}`}>
              {weightTotal.toFixed(2)} {Math.abs(weightTotal - 0.8) < 0.01 ? "" : "(sybil is negative, expect ~0.80)"}
            </span>
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
          {saving ? "Saving..." : "Save Scoring Settings"}
        </button>
      </div>
    </div>
  );
}
