"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { JobStatusResponse } from "@/lib/types";

// M7: Exponential backoff polling — starts fast, slows down for long jobs
const INITIAL_INTERVAL = 2000; // 2s
const MAX_INTERVAL = 10000; // 10s
const BACKOFF_FACTOR = 1.3;

export function useJobStatus(jobId: string | null) {
  const [status, setStatus] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const intervalRef = useRef(INITIAL_INTERVAL);

  const fetchStatus = useCallback(async () => {
    if (!jobId) return;

    try {
      const res = await fetch(`/api/jobs/${jobId}/status`);
      if (!res.ok) throw new Error(`Status ${res.status}`);
      const data: JobStatusResponse = await res.json();
      setStatus(data);
      setError(null);

      if (data.status === "COMPLETED" || data.status === "FAILED") {
        // Stop polling on terminal state
        return;
      }

      // Schedule next poll with backoff
      intervalRef.current = Math.min(
        intervalRef.current * BACKOFF_FACTOR,
        MAX_INTERVAL
      );
      timeoutRef.current = setTimeout(fetchStatus, intervalRef.current);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch status"
      );
      // Still retry on error, but with backoff
      intervalRef.current = Math.min(
        intervalRef.current * BACKOFF_FACTOR,
        MAX_INTERVAL
      );
      timeoutRef.current = setTimeout(fetchStatus, intervalRef.current);
    }
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;

    intervalRef.current = INITIAL_INTERVAL;
    fetchStatus();

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [jobId, fetchStatus]);

  return { status, error };
}
