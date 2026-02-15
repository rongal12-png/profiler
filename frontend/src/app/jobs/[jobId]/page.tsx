"use client";

import { useParams } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import { useJobStatus } from "@/hooks/useJobStatus";
import ProgressTracker from "@/components/ProgressTracker";
import ReportViewer from "@/components/ReportViewer";

export default function JobPage() {
  const params = useParams();
  const jobId = params.jobId as string;
  const { status, error } = useJobStatus(jobId);

  // Enrich localStorage with latest job data
  useEffect(() => {
    if (!status) return;
    try {
      const stored = localStorage.getItem("recentJobs");
      if (!stored) return;
      const jobs = JSON.parse(stored);
      if (!Array.isArray(jobs)) return;
      const idx = jobs.findIndex((j: { id: number }) => String(j.id) === jobId);
      if (idx >= 0) {
        jobs[idx] = {
          ...jobs[idx],
          status: status.status,
          projectName: status.project_name || jobs[idx].projectName,
          walletCount: status.total_wallets,
          createdAt: status.created_at || jobs[idx].createdAt,
        };
        localStorage.setItem("recentJobs", JSON.stringify(jobs));
      }
    } catch { /* ignore */ }
  }, [status, jobId]);

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
        Back to Home
      </Link>

      <div className="flex items-baseline gap-3 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {status?.project_name
            ? `${status.project_name} — Job #${jobId}`
            : `Job #${jobId}`}
        </h1>
        {status && (
          <span className="text-sm text-gray-500">
            Created {new Date(status.created_at).toLocaleString()}
          </span>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
          <p className="text-red-700">
            Error connecting to the analysis service: {error}
          </p>
        </div>
      )}

      {!status && !error && (
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-600">Loading job status...</p>
        </div>
      )}

      {status &&
        (status.status === "PENDING" || status.status === "IN_PROGRESS") && (
          <ProgressTracker status={status} />
        )}

      {status && status.status === "COMPLETED" && (
        <ReportViewer jobId={status.job_id} />
      )}

      {status && status.status === "FAILED" && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-red-800 mb-2">
            Analysis Failed
          </h2>
          <p className="text-red-600">
            {status.result || "An unknown error occurred during analysis."}
          </p>
        </div>
      )}
    </div>
  );
}
