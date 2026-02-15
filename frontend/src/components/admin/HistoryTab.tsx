"use client";

import { useState, useEffect } from "react";
import type { SettingsHistoryEntry } from "@/lib/types";
import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";

interface Props {
  fetchHistory: () => Promise<SettingsHistoryEntry[]>;
  onActivate: (versionId: number) => Promise<void>;
}

export default function HistoryTab({ fetchHistory, onActivate }: Props) {
  const [history, setHistory] = useState<SettingsHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [activating, setActivating] = useState<number | null>(null);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await fetchHistory();
      setHistory(data);
    } catch {
      setMessage({ type: "error", text: "Failed to load history" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadHistory(); }, []);

  const handleActivate = async (id: number) => {
    setActivating(id);
    setMessage(null);
    try {
      await onActivate(id);
      setMessage({ type: "success", text: `Version activated successfully` });
      await loadHistory();
    } catch (e) {
      setMessage({ type: "error", text: e instanceof Error ? e.message : "Failed to activate" });
    } finally {
      setActivating(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {message && (
        <div className={`p-3 rounded-lg text-sm ${message.type === "success" ? "bg-green-50 text-green-700 border border-green-200" : "bg-red-50 text-red-700 border border-red-200"}`}>
          {message.text}
        </div>
      )}

      {history.length === 0 ? (
        <Card>
          <p className="text-gray-500 text-center py-8">No settings history found</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {history.map((entry) => (
            <div key={entry.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div
                className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
                onClick={() => setExpandedId(expandedId === entry.id ? null : entry.id)}
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-mono text-gray-500">v{entry.version}</span>
                  {entry.is_active && <Badge label="Active" color="green" />}
                  <Badge label={entry.scope} color="blue" />
                  {entry.scope_key && <span className="text-xs text-gray-400">({entry.scope_key})</span>}
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-xs text-gray-500">{new Date(entry.created_at).toLocaleString()}</p>
                    {entry.notes && <p className="text-xs text-gray-400">{entry.notes}</p>}
                  </div>
                  {!entry.is_active && (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleActivate(entry.id); }}
                      disabled={activating === entry.id}
                      className="px-3 py-1 text-xs bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 disabled:opacity-50 font-medium"
                    >
                      {activating === entry.id ? "..." : "Activate"}
                    </button>
                  )}
                  <svg
                    className={`w-4 h-4 text-gray-400 transition-transform ${expandedId === entry.id ? "rotate-180" : ""}`}
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              {expandedId === entry.id && (
                <div className="border-t border-gray-200 p-4 bg-gray-50">
                  <pre className="text-xs text-gray-600 overflow-auto max-h-64 bg-gray-900 text-gray-100 p-4 rounded-lg">
                    {JSON.stringify(entry.settings_json, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
