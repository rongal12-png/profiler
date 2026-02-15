"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import FileUpload from "@/components/FileUpload";
import Badge from "@/components/ui/Badge";
import type { RecentJob } from "@/lib/types";

const CHAINS = [
  { name: "Ethereum", color: "indigo" },
  { name: "Base", color: "blue" },
  { name: "Arbitrum", color: "cyan" },
  { name: "Polygon", color: "indigo" },
  { name: "Solana", color: "green" },
] as const;

export default function HomePage() {
  const [recentJobs, setRecentJobs] = useState<RecentJob[]>([]);
  const [projectName, setProjectName] = useState("");

  useEffect(() => {
    const stored = localStorage.getItem("recentJobs");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        // Handle old format (number[]) and new format (RecentJob[])
        if (Array.isArray(parsed) && parsed.length > 0) {
          if (typeof parsed[0] === "number") {
            setRecentJobs(parsed.map((id: number) => ({ id, projectName: "Project", status: "COMPLETED" as const, createdAt: "", walletCount: 0 })));
          } else {
            setRecentJobs(parsed);
          }
        }
      } catch {
        // ignore invalid localStorage data
      }
    }
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
            <Badge key={chain.name} label={chain.name} color={chain.color as "indigo" | "blue" | "cyan" | "green"} />
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
              <div>0x73BCEb1Cd57C711f...,ethereum</div>
              <div>EPjFWdd5AufqSSqe...,solana</div>
              <div>0xaf2358e9868326...,polygon</div>
            </div>
          </div>

          {/* Recent Jobs */}
          {recentJobs.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Recent Jobs
              </h2>
              <div className="space-y-2">
                {recentJobs.map((job) => (
                  <Link
                    key={job.id}
                    href={`/jobs/${job.id}`}
                    className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
                  >
                    <div className="min-w-0">
                      <p className="font-medium text-gray-700 truncate">
                        {job.projectName || `Job #${job.id}`}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-gray-400">#{job.id}</span>
                        {job.walletCount > 0 && (
                          <span className="text-xs text-gray-400">{job.walletCount} wallets</span>
                        )}
                        {job.createdAt && (
                          <span className="text-xs text-gray-400">
                            {new Date(job.createdAt).toLocaleDateString()}
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
                          job.status === "IN_PROGRESS" ? "blue" : "yellow"
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
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
