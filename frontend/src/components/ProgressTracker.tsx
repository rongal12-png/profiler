"use client";

import { JobStatusResponse } from "@/lib/types";
import { useState, useEffect } from "react";

interface Props {
  status: JobStatusResponse;
  onAction?: () => void;
}

const statusConfig: Record<string, { color: string; bg: string; label: string }> = {
  PENDING:     { color: "text-yellow-800", bg: "bg-yellow-100", label: "Pending" },
  IN_PROGRESS: { color: "text-blue-800",   bg: "bg-blue-100",   label: "Analyzing" },
  PAUSED:      { color: "text-orange-800", bg: "bg-orange-100", label: "Paused" },
  STOPPED:     { color: "text-gray-800",   bg: "bg-gray-100",   label: "Stopped" },
  COMPLETED:   { color: "text-green-800",  bg: "bg-green-100",  label: "Completed" },
  FAILED:      { color: "text-red-800",    bg: "bg-red-100",    label: "Failed" },
};

function formatElapsedTime(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return "00:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  if (mins >= 60) {
    const hours = Math.floor(mins / 60);
    const remainingMins = mins % 60;
    return `${hours}:${String(remainingMins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

export default function ProgressTracker({ status, onAction }: Props) {
  const [currentElapsed, setCurrentElapsed] = useState<number | null>(status.elapsed_seconds);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const progress =
    status.total_wallets > 0
      ? Math.round((status.wallets_processed / status.total_wallets) * 100)
      : 0;

  const config = statusConfig[status.status] || statusConfig.PENDING;

  useEffect(() => {
    if (status.status !== "IN_PROGRESS" || !status.started_at) {
      setCurrentElapsed(status.elapsed_seconds);
      return;
    }
    setCurrentElapsed(status.elapsed_seconds);
    const interval = setInterval(() => {
      const startTime = new Date(status.started_at!).getTime();
      const now = Date.now();
      setCurrentElapsed((now - startTime) / 1000);
    }, 1000);
    return () => clearInterval(interval);
  }, [status]);

  const handleAction = async (action: "pause" | "resume" | "stop") => {
    setActionLoading(action);
    try {
      await fetch(`/api/jobs/${status.job_id}/${action}`, { method: "POST" });
      onAction?.();
    } finally {
      setActionLoading(null);
    }
  };

  const progressBarColor =
    status.status === "PAUSED"  ? "bg-orange-400" :
    status.status === "STOPPED" ? "bg-gray-400" :
    "bg-blue-600";

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Analysis Progress</h2>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.color}`}>
          {config.label}
        </span>
      </div>

      {/* Timer */}
      {currentElapsed !== null && status.started_at && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm font-medium text-gray-700">זמן ניתוח</span>
            </div>
            <div className="font-mono text-2xl font-bold text-blue-900">
              {formatElapsedTime(currentElapsed)}
            </div>
          </div>
        </div>
      )}

      {/* Progress bar */}
      <div className="space-y-2">
        <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
          <div
            className={`${progressBarColor} h-3 rounded-full transition-all duration-700 ease-out`}
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between text-sm text-gray-600">
          <span>{status.wallets_processed} / {status.total_wallets} wallets</span>
          <span>{progress}%</span>
        </div>
      </div>

      {/* Status message */}
      {status.status === "PENDING" && (
        <p className="text-sm text-gray-500">Job is queued and will start processing shortly...</p>
      )}
      {status.status === "IN_PROGRESS" && (
        <div className="flex items-center gap-2 text-sm text-blue-700">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span>Analyzing wallets on-chain...</span>
        </div>
      )}
      {status.status === "PAUSED" && (
        <p className="text-sm text-orange-700">Job is paused. Click Resume to continue analysis.</p>
      )}

      {/* Control buttons */}
      {(status.status === "IN_PROGRESS" || status.status === "PAUSED") && (
        <div className="flex gap-3 pt-1 border-t border-gray-100">
          {status.status === "IN_PROGRESS" && (
            <button
              onClick={() => handleAction("pause")}
              disabled={actionLoading !== null}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-orange-700 bg-orange-50 border border-orange-200 rounded-lg hover:bg-orange-100 disabled:opacity-50 transition-colors"
            >
              {actionLoading === "pause" ? (
                <div className="w-3.5 h-3.5 border-2 border-orange-600 border-t-transparent rounded-full animate-spin" />
              ) : (
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
                </svg>
              )}
              השהה
            </button>
          )}
          {status.status === "PAUSED" && (
            <button
              onClick={() => handleAction("resume")}
              disabled={actionLoading !== null}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 disabled:opacity-50 transition-colors"
            >
              {actionLoading === "resume" ? (
                <div className="w-3.5 h-3.5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              ) : (
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              )}
              המשך
            </button>
          )}
          <button
            onClick={() => handleAction("stop")}
            disabled={actionLoading !== null}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-700 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 disabled:opacity-50 transition-colors"
          >
            {actionLoading === "stop" ? (
              <div className="w-3.5 h-3.5 border-2 border-red-600 border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 6h12v12H6z"/>
              </svg>
            )}
            עצור
          </button>
        </div>
      )}
    </div>
  );
}
