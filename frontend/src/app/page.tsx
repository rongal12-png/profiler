"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import FileUpload from "@/components/FileUpload";
import Badge from "@/components/ui/Badge";

interface JobListItem {
  job_id: number;
  status: string;
  project_name: string | null;
  total_wallets: number;
  wallets_processed: number;
  created_at: string | null;
}

const CHAINS = [
  { name: "Ethereum", color: "indigo" },
  { name: "Base", color: "blue" },
  { name: "Arbitrum", color: "cyan" },
  { name: "Polygon", color: "indigo" },
  { name: "Optimism", color: "red" },
  { name: "BSC", color: "yellow" },
  { name: "Avalanche", color: "red" },
  { name: "Fantom", color: "blue" },
  { name: "Solana", color: "green" },
] as const;

export default function HomePage() {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [projectName, setProjectName] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/jobs")
      .then((res) => {
        if (!res.ok) throw new Error(`Jobs API returned ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (Array.isArray(data)) setJobs(data);
      })
      .catch((err) => {
        console.error("Failed to load jobs:", err);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      {/* Hero */}
      <div className="text-center mb-10 bg-gradient-to-b from-blue-50 to-transparent rounded-2xl py-10 px-6 -mx-6">
        <h1 className="text-4xl font-bold text-gray-900 mb-3">
          Wallet Intelligence
        </h1>
        <p className="text-gray-600 text-lg max-w-2xl mx-auto">
          Upload a CSV of wallet addresses to generate community quality scores,
          investment intelligence, risk analysis, and actionable insights.
        </p>
        <div className="flex justify-center gap-2 mt-4">
          {CHAINS.map((chain) => (
            <Badge key={chain.name} label={chain.name} color={chain.color as "indigo" | "blue" | "cyan" | "green" | "red" | "yellow"} />
          ))}
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Left: Upload form (3 cols) */}
        <div className="lg:col-span-3">
          <div className="mb-6">
            <label
              htmlFor="projectName"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Project Name
            </label>
            <input
              id="projectName"
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="e.g. Uniswap, Aave, My Protocol"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors text-gray-900 placeholder-gray-400"
            />
          </div>

          <FileUpload projectName={projectName} />
        </div>

        {/* Right: CSV guide + Recent jobs (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* CSV Format */}
          <div className="p-4 bg-white border border-gray-200 rounded-xl">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
              CSV Format
            </h3>
            <div className="bg-gray-50 rounded-lg p-3 font-mono text-sm text-gray-700">
              <div className="text-gray-400">address,chain</div>
              <div>0x73BCEb1Cd57C711f...,<span className="text-blue-600 font-semibold">evm</span></div>
              <div>EPjFWdd5AufqSSqe...,solana</div>
              <div>0xaf2358e9868326...,ethereum</div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Use <span className="font-mono font-semibold text-blue-600">evm</span> to scan across Ethereum, Base, Arbitrum, BSC &amp; Polygon automatically.
            </p>
          </div>

          {/* Recent Jobs */}
          <div>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Recent Jobs
            </h2>
            {loading ? (
              <p className="text-sm text-gray-400">Loading...</p>
            ) : jobs.length === 0 ? (
              <p className="text-sm text-gray-400">No jobs yet. Upload a CSV to get started.</p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {jobs.map((job) => (
                  <Link
                    key={job.job_id}
                    href={`/jobs/${job.job_id}`}
                    className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
                  >
                    <div className="min-w-0">
                      <p className="font-medium text-gray-700 truncate">
                        {job.project_name || `Job #${job.job_id}`}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-gray-400">#{job.job_id}</span>
                        <span className="text-xs text-gray-400">{job.total_wallets} wallets</span>
                        {job.created_at && (
                          <span className="text-xs text-gray-400">
                            {new Date(job.created_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        label={job.status || "UNKNOWN"}
                        color={
                          job.status === "COMPLETED" ? "green" :
                          job.status === "FAILED" ? "red" :
                          job.status === "IN_PROGRESS" ? "blue" : job.status === "PAUSED" ? "yellow" : job.status === "STOPPED" ? "gray" : "yellow"
                        }
                      />
                      <svg
                        className="w-4 h-4 text-gray-400 flex-shrink-0"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
