"use client";

import { useState, useEffect, useRef } from "react";
import { JobStatusResponse } from "@/lib/types";

const POLL_INTERVAL = 3000;

export function useJobStatus(jobId: string | null) {
  const [status, setStatus] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const fetchStatus = async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}/status`);
        if (!res.ok) throw new Error(`Status ${res.status}`);
        const data: JobStatusResponse = await res.json();
        setStatus(data);
        setError(null);

        if (data.status === "COMPLETED" || data.status === "FAILED") {
          if (intervalRef.current) clearInterval(intervalRef.current);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch status"
        );
      }
    };

    fetchStatus();
    intervalRef.current = setInterval(fetchStatus, POLL_INTERVAL);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [jobId]);

  return { status, error };
}
