"use client";

import { useState, useEffect } from "react";
import type { SettingsData, SanctionsListStatus } from "@/lib/types";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";

interface Props {
  settings: SettingsData;
  sanctionsStatus: SanctionsListStatus[];
  onSave: (settingsJson: Record<string, unknown>) => Promise<void>;
  onUpdateSanctions: () => Promise<Record<string, unknown>>;
  onRefreshStatus: () => Promise<void>;
}

export default function SanctionsTab({ settings, sanctionsStatus, onSave, onUpdateSanctions, onRefreshStatus }: Props) {
  const s = settings.settings.sanctions;
  const [enabled, setEnabled] = useState(s.enabled);
  const [lists, setLists] = useState({ ...s.lists });
  const [actionOnHit, setActionOnHit] = useState(s.action_on_hit);
  const [autoUpdateHours, setAutoUpdateHours] = useState(s.auto_update_hours);
  const [saving, setSaving] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    setEnabled(s.enabled);
    setLists({ ...s.lists });
    setActionOnHit(s.action_on_hit);
    setAutoUpdateHours(s.auto_update_hours);
  }, [s]);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await onSave({ sanctions: { enabled, lists, action_on_hit: actionOnHit, auto_update_hours: autoUpdateHours } });
      setMessage({ type: "success", text: "Sanctions settings saved!" });
    } catch (e) {
      setMessage({ type: "error", text: e instanceof Error ? e.message : "Save failed" });
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async () => {
    setUpdating(true);
    setMessage(null);
    try {
      const result = await onUpdateSanctions();
      setMessage({ type: "success", text: `Sanctions update completed: ${JSON.stringify(result)}` });
      await onRefreshStatus();
    } catch (e) {
      setMessage({ type: "error", text: e instanceof Error ? e.message : "Update failed" });
    } finally {
      setUpdating(false);
    }
  };

  const listNames: Record<string, string> = {
    ofac_sdn: "OFAC SDN (US)",
    eu_consolidated: "EU Consolidated",
    israel_nbctf: "Israel NBCTF",
  };

  return (
    <div className="space-y-6">
      {/* Master Toggle */}
      <Card title="Sanctions Screening">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-gray-800">Enable Sanctions Screening</p>
            <p className="text-sm text-gray-500">Check wallets against international sanctions lists</p>
          </div>
          <button
            onClick={() => setEnabled(!enabled)}
            className={`relative w-14 h-7 rounded-full transition-colors ${enabled ? "bg-blue-600" : "bg-gray-300"}`}
          >
            <div className={`absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full transition-transform shadow ${enabled ? "translate-x-7" : ""}`} />
          </button>
        </div>
      </Card>

      {/* Per-list toggles */}
      <Card title="Sanctions Lists">
        <div className="space-y-3">
          {Object.entries(lists).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
              <span className="text-sm font-medium text-gray-700">{listNames[key] || key}</span>
              <button
                onClick={() => setLists({ ...lists, [key]: !value })}
                className={`relative w-11 h-6 rounded-full transition-colors ${value ? "bg-blue-600" : "bg-gray-300"}`}
              >
                <div className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow ${value ? "translate-x-5" : ""}`} />
              </button>
            </div>
          ))}
        </div>
      </Card>

      {/* Action on Hit */}
      <Card title="Action on Hit">
        <div className="flex gap-3">
          {["flag", "exclude", "both"].map((action) => (
            <label
              key={action}
              className={`flex-1 cursor-pointer rounded-lg border-2 p-3 text-center text-sm font-medium transition-colors ${
                actionOnHit === action ? "border-blue-500 bg-blue-50 text-blue-700" : "border-gray-200 text-gray-600 hover:bg-gray-50"
              }`}
            >
              <input
                type="radio"
                name="actionOnHit"
                value={action}
                checked={actionOnHit === action}
                onChange={() => setActionOnHit(action)}
                className="sr-only"
              />
              {action === "flag" ? "Flag Only" : action === "exclude" ? "Exclude" : "Flag + Exclude"}
            </label>
          ))}
        </div>
      </Card>

      {/* Auto-update interval */}
      <Card title="Auto-Update Interval">
        <div className="flex items-center gap-3">
          <input
            type="number"
            value={autoUpdateHours}
            onChange={(e) => setAutoUpdateHours(Number(e.target.value))}
            min={1}
            className="w-24 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          />
          <span className="text-sm text-gray-500">hours between automatic updates</span>
        </div>
      </Card>

      {/* List Status */}
      {sanctionsStatus.length > 0 && (
        <Card title="List Status">
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">List</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Records</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Last Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sanctionsStatus.map((list) => (
                  <tr key={list.list_name} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-medium text-gray-700">{listNames[list.list_name] || list.list_name}</td>
                    <td className="px-3 py-2">
                      <Badge
                        label={list.status}
                        color={list.status === "active" ? "green" : list.status === "updating" ? "yellow" : "gray"}
                      />
                    </td>
                    <td className="px-3 py-2 text-gray-600">{list.record_count.toLocaleString()}</td>
                    <td className="px-3 py-2 text-gray-500 text-xs">
                      {list.last_updated ? new Date(list.last_updated).toLocaleString() : "Never"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button
            onClick={handleUpdate}
            disabled={updating}
            className="mt-4 px-4 py-2 bg-amber-600 text-white text-sm rounded-lg hover:bg-amber-700 disabled:opacity-50 font-medium"
          >
            {updating ? "Updating..." : "Update All Lists Now"}
          </button>
        </Card>
      )}

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
          {saving ? "Saving..." : "Save Sanctions Settings"}
        </button>
      </div>
    </div>
  );
}
