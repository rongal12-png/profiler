"use client";

import { useState, useEffect } from "react";

interface Props {
  jobId: number;
}

export default function FullReportTab({ jobId }: Props) {
  const [html, setHtml] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`/api/jobs/${jobId}/report?format=html`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load HTML report");
        return res.text();
      })
      .then((text) => {
        if (cancelled) return;
        // Extract body content from full HTML document
        const bodyMatch = text.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
        setHtml(bodyMatch ? bodyMatch[1] : text);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [jobId]);

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
    <div
      className="report-content bg-white rounded-xl border border-gray-200 p-8 max-w-none"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
