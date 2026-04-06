"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import type { ProjectSummary } from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  COMPLETED: "bg-green-100 text-green-800",
  IN_PROGRESS: "bg-blue-100 text-blue-800",
  PAUSED: "bg-yellow-100 text-yellow-800",
  STOPPED: "bg-gray-100 text-gray-700",
  FAILED: "bg-red-100 text-red-800",
};

function StatusBadge({ status }: { status: string | null }) {
  if (!status) return <span className="text-gray-400 text-xs">No runs yet</span>;
  const cls = STATUS_COLORS[status] ?? "bg-gray-100 text-gray-700";
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>{status}</span>;
}

function fmtDate(d: string | null) {
  if (!d) return "—";
  return new Date(d).toLocaleString();
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  const fetchProjects = () => {
    fetch("/api/projects")
      .then((r) => r.json())
      .then((data) => { setProjects(Array.isArray(data) ? data : []); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { fetchProjects(); }, []);

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <p className="text-sm text-gray-500 mt-1">
            Each project stores a fixed wallet list. Run a new analysis any time to track changes over time.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
        >
          + New Project
        </button>
      </div>

      {showCreate && (
        <CreateProjectCard
          onClose={() => setShowCreate(false)}
          onCreated={(id) => { setShowCreate(false); fetchProjects(); window.location.href = `/projects/${id}`; }}
        />
      )}

      {loading ? (
        <div className="text-center py-16 text-gray-400">Loading…</div>
      ) : projects.length === 0 ? (
        <div className="text-center py-16 border-2 border-dashed border-gray-200 rounded-xl text-gray-400">
          <div className="text-4xl mb-3">📂</div>
          <p className="font-medium">No projects yet</p>
          <p className="text-sm mt-1">Create your first project to start tracking a wallet list over time.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.id}`}
              className="block border border-gray-200 rounded-xl p-5 bg-white hover:shadow-md hover:border-blue-300 transition-all"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <h2 className="font-semibold text-gray-900 text-lg truncate">{p.name}</h2>
                    <StatusBadge status={p.last_status} />
                  </div>
                  {p.description && (
                    <p className="text-sm text-gray-500 mb-2 line-clamp-2">{p.description}</p>
                  )}
                  <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-500">
                    <span><span className="font-medium text-gray-700">{p.wallet_count.toLocaleString()}</span> wallets</span>
                    <span><span className="font-medium text-gray-700">{p.run_count}</span> run{p.run_count !== 1 ? "s" : ""}</span>
                    <span>Last run: <span className="font-medium text-gray-700">{fmtDate(p.last_run_at)}</span></span>
                    <span>Created: {fmtDate(p.created_at)}</span>
                  </div>
                </div>
                <svg className="w-5 h-5 text-gray-400 flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function CreateProjectCard({ onClose, onCreated }: { onClose: () => void; onCreated: (id: number) => void }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) { setError("Project name is required."); return; }
    if (!file) { setError("Please upload a CSV file."); return; }
    setError(""); setLoading(true);
    const fd = new FormData();
    fd.append("name", name.trim());
    fd.append("description", description.trim());
    fd.append("file", file);
    try {
      const res = await fetch("/api/projects", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || "Failed to create project."); return; }
      onCreated(data.id);
    } catch { setError("Network error."); }
    finally { setLoading(false); }
  }

  return (
    <div className="border border-blue-200 bg-blue-50 rounded-xl p-6">
      <h3 className="font-semibold text-gray-900 mb-4">New Project</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Project Name *</label>
          <input
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="e.g. RAIN Community, Protocol XYZ Holders"
            value={name} onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <input
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="Optional description"
            value={description} onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Wallet List (CSV) *</label>
          <p className="text-xs text-gray-500 mb-2">CSV must have <code>address</code> and <code>chain</code> columns. The same list will be used for every run.</p>
          <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <button type="button" onClick={() => fileRef.current?.click()}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white hover:bg-gray-50">
            {file ? `✓ ${file.name}` : "Choose CSV file…"}
          </button>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="flex gap-3">
          <button type="submit" disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {loading ? "Creating…" : "Create Project"}
          </button>
          <button type="button" onClick={onClose}
            className="px-4 py-2 border border-gray-300 text-gray-700 text-sm rounded-lg hover:bg-gray-50">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
