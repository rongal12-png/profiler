import { useCallback } from "react";
import type { SettingsData, SanctionsListStatus, SettingsHistoryEntry } from "@/lib/types";

export function useAdminAPI(apiKey: string) {
  const headers = useCallback(() => ({
    "X-API-Key": apiKey,
    "Content-Type": "application/json",
  }), [apiKey]);

  const getSettings = useCallback(async (): Promise<SettingsData> => {
    const res = await fetch("/api/admin/settings", { headers: { "X-API-Key": apiKey } });
    if (!res.ok) throw new Error("Failed to fetch settings");
    return res.json();
  }, [apiKey]);

  const saveSettings = useCallback(async (settingsJson: Record<string, unknown>, notes?: string): Promise<void> => {
    const res = await fetch("/api/admin/settings", {
      method: "PUT",
      headers: headers(),
      body: JSON.stringify({ scope: "global", settings_json: settingsJson, notes: notes || "Updated via admin UI" }),
    });
    if (!res.ok) throw new Error("Failed to save settings");
  }, [headers]);

  const getSettingsHistory = useCallback(async (limit = 20): Promise<SettingsHistoryEntry[]> => {
    const res = await fetch(`/api/admin/settings/history?limit=${limit}`, { headers: { "X-API-Key": apiKey } });
    if (!res.ok) throw new Error("Failed to fetch history");
    return res.json();
  }, [apiKey]);

  const activateVersion = useCallback(async (versionId: number): Promise<void> => {
    const res = await fetch(`/api/admin/settings/${versionId}/activate`, {
      method: "POST",
      headers: { "X-API-Key": apiKey },
    });
    if (!res.ok) throw new Error("Failed to activate version");
  }, [apiKey]);

  const getSanctionsStatus = useCallback(async (): Promise<SanctionsListStatus[]> => {
    const res = await fetch("/api/admin/sanctions/status", { headers: { "X-API-Key": apiKey } });
    if (!res.ok) throw new Error("Failed to fetch sanctions status");
    return res.json();
  }, [apiKey]);

  const triggerSanctionsUpdate = useCallback(async (): Promise<Record<string, unknown>> => {
    const res = await fetch("/api/admin/sanctions/update", {
      method: "POST",
      headers: { "X-API-Key": apiKey },
    });
    if (!res.ok) throw new Error("Failed to trigger sanctions update");
    return res.json();
  }, [apiKey]);

  return { getSettings, saveSettings, getSettingsHistory, activateVersion, getSanctionsStatus, triggerSanctionsUpdate };
}
