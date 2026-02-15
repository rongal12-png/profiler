"use client";

import { JobStatusResponse } from "@/lib/types";
import { useState, useEffect } from "react";

interface Props {
  status: JobStatusResponse;
}

const statusConfig: Record<
  string,
  { color: string; bg: string; label: string }
> = {
  PENDING: { color: "text-yellow-800", bg: "bg-yellow-100", label: "Pending" },
  IN_PROGRESS: {
    color: "text-blue-800",
    bg: "bg-blue-100",
    label: "Analyzing",
  },
  COMPLETED: {
    color: "text-green-800",
    bg: "bg-green-100",
    label: "Completed",
  },
  FAILED: { color: "text-red-800", bg: "bg-red-100", label: "Failed" },
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

export default function ProgressTracker({ status }: Props) {
  const [currentElapsed, setCurrentElapsed] = useState<number | null>(
    status.elapsed_seconds
  );

  const progress =
    status.total_wallets > 0
      ? Math.round((status.wallets_processed / status.total_wallets) * 100)
      : 0;

  const config = statusConfig[status.status] || statusConfig.PENDING;

  // Update timer every second for in-progress jobs
  useEffect(() => {
    if (status.status !== "IN_PROGRESS" || !status.started_at) {
      setCurrentElapsed(status.elapsed_seconds);
      return;
    }

    // Initial value
    setCurrentElapsed(status.elapsed_seconds);

    // Tick every second
    const interval = setInterval(() => {
      const startTime = new Date(status.started_at!).getTime();
      const now = Date.now();
      const elapsed = (now - startTime) / 1000;
      setCurrentElapsed(elapsed);
    }, 1000);

    return () => clearInterval(interval);
  }, [status]);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          Analysis Progress
        </h2>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.color}`}
        >
          {config.label}
        </span>
      </div>

      {/* Timer Display */}
      {currentElapsed !== null && status.started_at && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg
                className="w-5 h-5 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span className="text-sm font-medium text-gray-700">
                זמן ניתוח
              </span>
            </div>
            <div className="font-mono text-2xl font-bold text-blue-900">
              {formatElapsedTime(currentElapsed)}
            </div>
          </div>
        </div>
      )}

      <div className="space-y-2">
        <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
          <div
            className="bg-blue-600 h-3 rounded-full transition-all duration-700 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between text-sm text-gray-600">
          <span>
            {status.wallets_processed} / {status.total_wallets} wallets
          </span>
          <span>{progress}%</span>
        </div>
      </div>

      {status.status === "PENDING" && (
        <p className="text-sm text-gray-500">
          Job is queued and will start processing shortly...
        </p>
      )}

      {status.status === "IN_PROGRESS" && (
        <div className="flex items-center gap-2 text-sm text-blue-700">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span>Analyzing wallets on-chain...</span>
        </div>
      )}
    </div>
  );
}
