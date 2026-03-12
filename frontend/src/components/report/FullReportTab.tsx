"use client";

import { useState, useEffect } from "react";

interface Props {
  jobId: number;
}

export default function FullReportTab({ jobId }: Props) {
  const [html, setHtml] = useState<string | null>(null);
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editedMarkdown, setEditedMarkdown] = useState<string>("");
  const [downloadingEdited, setDownloadingEdited] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    // Fetch both HTML (for display) and Markdown (for editing) in parallel
    Promise.all([
      fetch(`/api/jobs/${jobId}/report?format=html`).then((r) => {
        if (!r.ok) throw new Error("Failed to load HTML report");
        return r.text();
      }),
      fetch(`/api/jobs/${jobId}/report?format=markdown`).then((r) => {
        if (!r.ok) throw new Error("Failed to load Markdown report");
        return r.text();
      }),
    ])
      .then(([htmlText, mdText]) => {
        if (cancelled) return;
        const bodyMatch = htmlText.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
        setHtml(bodyMatch ? bodyMatch[1] : htmlText);
        setMarkdown(mdText);
        setEditedMarkdown(mdText);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [jobId]);

  const handleEnterEdit = () => {
    setEditedMarkdown(markdown || "");
    setEditMode(true);
  };

  const handleCancelEdit = () => {
    setEditMode(false);
  };

  const handleDownloadEdited = async () => {
    setDownloadingEdited(true);
    try {
      const res = await fetch(`/api/jobs/${jobId}/report/custom-pdf`, {
        method: "POST",
        headers: { "Content-Type": "text/plain" },
        body: editedMarkdown,
      });
      if (!res.ok) throw new Error("PDF generation failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `edited-report-${jobId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Edited PDF download failed:", err);
      alert("Failed to generate PDF. Please try again.");
    } finally {
      setDownloadingEdited(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (!html) return null;

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center gap-3">
        {!editMode ? (
          <button
            onClick={handleEnterEdit}
            className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg font-medium text-sm transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Edit Report
          </button>
        ) : (
          <>
            <button
              onClick={handleDownloadEdited}
              disabled={downloadingEdited}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-medium text-sm transition-colors"
            >
              {downloadingEdited ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Generating PDF...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Download Edited PDF
                </>
              )}
            </button>
            <button
              onClick={handleCancelEdit}
              className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium text-sm transition-colors"
            >
              Cancel Editing
            </button>
            <span className="text-xs text-gray-400">
              Edit the Markdown below, then download as PDF
            </span>
          </>
        )}
      </div>

      {/* Content */}
      {editMode ? (
        <textarea
          value={editedMarkdown}
          onChange={(e) => setEditedMarkdown(e.target.value)}
          className="w-full h-[70vh] font-mono text-sm p-4 border border-gray-300 rounded-xl resize-y focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-gray-800 bg-gray-50"
          spellCheck={false}
        />
      ) : (
        <div
          className="report-content bg-white rounded-xl border border-gray-200 p-8 max-w-none"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      )}
    </div>
  );
}
