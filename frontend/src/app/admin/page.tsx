"use client";

import { useState, useCallback } from "react";
import type { SettingsData, SanctionsListStatus } from "@/lib/types";
import { useAdminAPI } from "@/hooks/useAdminAPI";
import Tabs from "@/components/ui/Tabs";
import ScoringTab from "@/components/admin/ScoringTab";
import SanctionsTab from "@/components/admin/SanctionsTab";
import IntelligenceTab from "@/components/admin/IntelligenceTab";
import HistoryTab from "@/components/admin/HistoryTab";

const ADMIN_TABS = [
  { id: "scoring", label: "Scoring" },
  { id: "sanctions", label: "Sanctions" },
  { id: "intelligence", label: "Intelligence & Report" },
  { id: "history", label: "History" },
];

export default function AdminPage() {
  const [apiKey, setApiKey] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [sanctionsStatus, setSanctionsStatus] = useState<SanctionsListStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("scoring");

  const api = useAdminAPI(apiKey);

  const handleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSettings();
      setSettings(data);
      const status = await api.getSanctionsStatus();
      setSanctionsStatus(status);
      setIsAuthenticated(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = useCallback(async (settingsJson: Record<string, unknown>) => {
    await api.saveSettings(settingsJson);
    const data = await api.getSettings();
    setSettings(data);
  }, [api]);

  const handleUpdateSanctions = useCallback(async () => {
    const result = await api.triggerSanctionsUpdate();
    return result;
  }, [api]);

  const handleRefreshSanctions = useCallback(async () => {
    const status = await api.getSanctionsStatus();
    setSanctionsStatus(status);
  }, [api]);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-200 w-full max-w-md">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Admin Login</h1>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter your admin API key"
              />
            </div>
            {error && (
              <div className="text-red-600 text-sm bg-red-50 p-3 rounded-lg border border-red-200">{error}</div>
            )}
            <button
              onClick={handleLogin}
              disabled={loading || !apiKey}
              className="w-full bg-blue-600 text-white py-2.5 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
            >
              {loading ? "Authenticating..." : "Login"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Admin Dashboard</h1>

        <Tabs tabs={ADMIN_TABS} activeTab={activeTab} onChange={setActiveTab} />

        <div className="mt-6">
          {activeTab === "scoring" && settings && (
            <ScoringTab settings={settings} onSave={handleSave} />
          )}
          {activeTab === "sanctions" && settings && (
            <SanctionsTab
              settings={settings}
              sanctionsStatus={sanctionsStatus}
              onSave={handleSave}
              onUpdateSanctions={handleUpdateSanctions}
              onRefreshStatus={handleRefreshSanctions}
            />
          )}
          {activeTab === "intelligence" && settings && (
            <IntelligenceTab settings={settings} onSave={handleSave} />
          )}
          {activeTab === "history" && (
            <HistoryTab
              fetchHistory={api.getSettingsHistory}
              onActivate={api.activateVersion}
            />
          )}
        </div>
      </div>
    </div>
  );
}
