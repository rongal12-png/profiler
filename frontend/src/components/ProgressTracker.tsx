"use client";

import { JobStatusResponse } from "@/lib/types";

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

export default function ProgressTracker({ status }: Props) {
  const progress =
    status.total_wallets > 0
      ? Math.round((status.wallets_processed / status.total_wallets) * 100)
      : 0;

  const config = statusConfig[status.status] || statusConfig.PENDING;

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
