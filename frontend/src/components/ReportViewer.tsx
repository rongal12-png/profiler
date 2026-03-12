"use client";

import { useState, useEffect } from "react";
import type { ProjectReport } from "@/lib/types";
import Tabs from "@/components/ui/Tabs";
import OverviewTab from "@/components/report/OverviewTab";
import WalletsTab from "@/components/report/WalletsTab";
import IntelligenceTab from "@/components/report/IntelligenceTab";
import RiskTab from "@/components/report/RiskTab";
import FullReportTab from "@/components/report/FullReportTab";

interface Props {
  jobId: number;
}

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "wallets", label: "Wallets" },
  { id: "intelligence", label: "Intelligence" },
  { id: "risk", label: "Risk" },
  { id: "report", label: "Full Report" },
];

export default function ReportViewer({ jobId }: Props) {
  const [report, setReport] = useState<ProjectReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/jobs/${jobId}/report?format=json`)
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.text().catch(() => "");
          let detail = "";
          try { detail = JSON.parse(body)?.detail || body; } catch { detail = body; }
          throw new Error(`Report error (HTTP ${res.status}): ${detail || "unknown error"}`);
        }
        return res.json();
      })
      .then((data: ProjectReport) => {
        if (!cancelled) setReport(data);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [jobId]);

  const downloadFile = async (format: "pdf" | "docx") => {
    setDownloading(format);
    try {
      const res = await fetch(`/api/jobs/${jobId}/report?format=${format}`);
      if (!res.ok) throw new Error(`${format.toUpperCase()} generation failed`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `wallet-report-${report?.reference_id || jobId}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(`${format.toUpperCase()} download failed:`, err);
    } finally {
      setDownloading(null);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-gray-600">Loading report...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <p className="text-red-700">{error || "Failed to load report."}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Download buttons */}
      <div className="flex flex-wrap gap-3">
        <DownloadButton label="PDF" format="pdf" downloading={downloading} onDownload={downloadFile} color="bg-blue-600 hover:bg-blue-700" />
        <DownloadButton label="Word" format="docx" downloading={downloading} onDownload={downloadFile} color="bg-indigo-600 hover:bg-indigo-700" />
        <a
          href={`/api/jobs/${jobId}/report?format=csv`}
          download={`wallet-report-${report.reference_id}.csv`}
          className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium text-sm"
        >
          CSV
        </a>
        <a
          href={`/api/jobs/${jobId}/report?format=json`}
          download={`wallet-report-${report.reference_id}.json`}
          className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium text-sm"
        >
          JSON
        </a>
        <a
          href={`/api/jobs/${jobId}/report?format=html`}
          download={`wallet-report-${report.reference_id}.html`}
          className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium text-sm"
        >
          HTML
        </a>
      </div>

      {/* Tabs */}
      <Tabs tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab content */}
      <div className="mt-4">
        {activeTab === "overview" && <OverviewTab report={report} />}
        {activeTab === "wallets" && <WalletsTab wallets={report.wallets} />}
        {activeTab === "intelligence" && <IntelligenceTab report={report} />}
        {activeTab === "risk" && <RiskTab report={report} />}
        {activeTab === "report" && <FullReportTab jobId={jobId} />}
      </div>
    </div>
  );
}

function DownloadButton({
  label,
  format,
  downloading,
  onDownload,
  color,
}: {
  label: string;
  format: "pdf" | "docx";
  downloading: string | null;
  onDownload: (f: "pdf" | "docx") => void;
  color: string;
}) {
  return (
    <button
      onClick={() => onDownload(format)}
      disabled={downloading !== null}
      className={`inline-flex items-center gap-2 px-4 py-2 text-white rounded-lg transition-colors disabled:opacity-50 font-medium text-sm ${color}`}
    >
      {downloading === format ? (
        <>
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          Generating...
        </>
      ) : (
        <>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {label}
        </>
      )}
    </button>
  );
}
