"use client";

import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";

interface Props {
  projectName: string;
}

export default function FileUpload({ projectName }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleUpload = useCallback(
    async (file: File) => {
      if (!file.name.endsWith(".csv")) {
        setError("Please upload a CSV file.");
        return;
      }

      if (!projectName.trim()) {
        setError("Please enter a project name first.");
        return;
      }

      setIsUploading(true);
      setError(null);

      const formData = new FormData();
      formData.append("file", file);
      formData.append("project_name", projectName.trim());

      try {
        const res = await fetch("/api/jobs/submit", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || "Upload failed");
        }

        const data = await res.json();

        const stored = localStorage.getItem("recentJobs");
        const recentJobs = stored ? JSON.parse(stored) : [];
        const newEntry = {
          id: data.job_id,
          projectName: projectName.trim(),
          status: "PENDING",
          createdAt: new Date().toISOString(),
          walletCount: 0,
        };
        recentJobs.unshift(newEntry);
        localStorage.setItem(
          "recentJobs",
          JSON.stringify(recentJobs.slice(0, 10))
        );

        router.push(`/jobs/${data.job_id}`);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setIsUploading(false);
      }
    },
    [router, projectName]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleUpload(file);
    },
    [handleUpload]
  );

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const onFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleUpload(file);
    },
    [handleUpload]
  );

  return (
    <div>
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
          transition-all duration-200
          ${
            isDragging
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 hover:border-gray-400 hover:bg-gray-50"
          }
          ${isUploading ? "pointer-events-none opacity-60" : ""}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={onFileSelect}
          className="hidden"
        />

        {isUploading ? (
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-600 font-medium">Uploading...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <svg
              className="w-12 h-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <div>
              <p className="text-gray-700 font-medium">
                Drop your CSV file here, or{" "}
                <span className="text-blue-600">browse</span>
              </p>
              <p className="text-sm text-gray-500 mt-1">
                CSV must contain &apos;address&apos; and &apos;chain&apos;
                columns
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}
