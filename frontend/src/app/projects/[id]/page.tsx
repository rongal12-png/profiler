"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import type { ProjectDetail, ProjectRun, JobStatus } from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  COMPLETED: "bg-green-100 text-green-800",
  IN_PROGRESS: "bg-blue-100 text-blue-800",
  PAUSED: "bg-yellow-100 text-yellow-800",
  STOPPED: "bg-gray-100 text-gray-700",
  FAILED: "bg-red-100 text-red-800",
  PENDING: "bg-purple-100 text-purple-800",
};

function StatusBadge({ status }: { status: string }) {
  const cls = STATUS_COLORS[status] ?? "bg-gray-100 text-gray-700";
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>{status}</span>;
}

function fmtDate(d: string | null) {
  if (!d) return "—";
  return new Date(d).toLocaleString();
}

function fmtDuration(s: number | null) {
  if (s == null) return "—";
  if (s < 60) return `${Math.round(s)}s`;
  const m = Math.floor(s / 60);
  const rem = Math.round(s % 60);
  return rem > 0 ? `${m}m ${rem}s` : `${m}m`;
}

function isActive(status: string) {
  return status === "IN_PROGRESS" || status === "PENDING";
}

export default function ProjectWorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState("");
  const [showEdit, setShowEdit] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [showNewList, setShowNewList] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchProject = async () => {
    try {
      const res = await fetch(`/api/projects/${id}`);
      if (!res.ok) {
        const d = await res.json();
        setError(d.detail || "Failed to load project.");
        setLoading(false);
        return;
      }
      const data: ProjectDetail = await res.json();
      setProject(data);
      setLoading(false);
      return data;
    } catch {
      setError("Network error loading project.");
      setLoading(false);
    }
  };

  // Poll while any run is active
  useEffect(() => {
    fetchProject();
  }, [id]);

  useEffect(() => {
    if (!project) return;
    const hasActive = project.runs.some((r) => isActive(r.status));
    if (hasActive && !pollRef.current) {
      pollRef.current = setInterval(fetchProject, 3000);
    } else if (!hasActive && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    return () => {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    };
  }, [project]);

  async function handleRun() {
    setRunError("");
    setRunning(true);
    try {
      const res = await fetch(`/api/projects/${id}/run`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) { setRunError(data.detail || "Failed to start run."); return; }
      await fetchProject();
    } catch { setRunError("Network error."); }
    finally { setRunning(false); }
  }

  if (loading) return <div className="max-w-5xl mx-auto px-6 py-16 text-center text-gray-400">Loading…</div>;
  if (error) return <div className="max-w-5xl mx-auto px-6 py-16 text-center text-red-600">{error}</div>;
  if (!project) return null;

  const activeRun = project.runs.find((r) => isActive(r.status));

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      {/* Back link */}
      <Link href="/projects" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        All Projects
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
          {project.description && <p className="text-sm text-gray-500 mt-1">{project.description}</p>}
          <div className="flex gap-4 mt-2 text-xs text-gray-500">
            <span><span className="font-medium text-gray-700">{project.wallet_count.toLocaleString()}</span> wallets</span>
            <span><span className="font-medium text-gray-700">{project.runs.length}</span> run{project.runs.length !== 1 ? "s" : ""}</span>
            <span>Created {fmtDate(project.created_at)}</span>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={() => setShowEdit(true)}
            className="px-3 py-2 border border-gray-300 text-gray-700 text-sm rounded-lg hover:bg-gray-50"
          >
            Edit
          </button>
          <button
            onClick={() => setShowNewList(true)}
            disabled={!!activeRun}
            className="px-3 py-2 border border-blue-300 text-blue-700 text-sm rounded-lg hover:bg-blue-50 disabled:opacity-50"
          >
            Upload new list
          </button>
          <button
            onClick={handleRun}
            disabled={running || !!activeRun}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {running ? "Starting…" : activeRun ? "Running…" : "▶ Run Now"}
          </button>
        </div>
      </div>

      {runError && <p className="text-sm text-red-600">{runError}</p>}

      {activeRun && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center gap-3">
          <svg className="w-4 h-4 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <span className="text-sm text-blue-800">
            Scan in progress — job #{activeRun.job_id}.{" "}
            {activeRun.wallets_processed > 0 && (
              <span>{activeRun.wallets_processed.toLocaleString()} / {(activeRun.total_wallets || project.wallet_count).toLocaleString()} wallets processed.</span>
            )}
          </span>
          <Link href={`/jobs/${activeRun.job_id}`} className="ml-auto text-xs text-blue-600 underline">
            View progress →
          </Link>
        </div>
      )}

      {/* Runs table */}
      <div>
        <h2 className="text-base font-semibold text-gray-900 mb-3">Run History</h2>
        {project.runs.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-xl text-gray-400">
            <p className="font-medium">No runs yet</p>
            <p className="text-sm mt-1">Click "Run Now" to start the first analysis.</p>
          </div>
        ) : (
          <div className="border border-gray-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Run</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Started</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Completed</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Duration</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Wallets</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {project.runs.map((run, idx) => (
                  <tr key={run.job_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-500">
                      #{run.job_id}
                      {idx === 0 && <span className="ml-2 text-xs text-gray-400">latest</span>}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={run.status} />
                    </td>
                    <td className="px-4 py-3 text-gray-700">{fmtDate(run.created_at)}</td>
                    <td className="px-4 py-3 text-gray-700">{fmtDate(run.completed_at)}</td>
                    <td className="px-4 py-3 text-gray-700">{fmtDuration(run.elapsed_seconds)}</td>
                    <td className="px-4 py-3 text-gray-700">
                      {run.wallets_processed > 0
                        ? `${run.wallets_processed.toLocaleString()} / ${(run.total_wallets || project.wallet_count).toLocaleString()}`
                        : (run.total_wallets || project.wallet_count).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {run.status === "COMPLETED" ? (
                        <Link
                          href={`/jobs/${run.job_id}`}
                          className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                        >
                          View Report →
                        </Link>
                      ) : isActive(run.status) ? (
                        <Link
                          href={`/jobs/${run.job_id}`}
                          className="text-xs text-blue-600 hover:text-blue-800"
                        >
                          View Progress →
                        </Link>
                      ) : (
                        <Link
                          href={`/jobs/${run.job_id}`}
                          className="text-xs text-gray-500 hover:text-gray-700"
                        >
                          Details →
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Danger zone */}
      <div className="border border-red-200 rounded-xl p-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-700">Delete Project</p>
          <p className="text-xs text-gray-500 mt-0.5">Permanently removes the project and all associated run history.</p>
        </div>
        <button
          onClick={() => setShowDelete(true)}
          className="px-3 py-2 border border-red-300 text-red-600 text-sm rounded-lg hover:bg-red-50"
        >
          Delete
        </button>
      </div>

      {/* Upload new list & run modal */}
      {showNewList && (
        <NewListModal
          projectId={project.id}
          currentCount={project.wallet_count}
          onClose={() => setShowNewList(false)}
          onStarted={() => { setShowNewList(false); fetchProject(); }}
        />
      )}

      {/* Edit modal */}
      {showEdit && (
        <EditProjectModal
          project={project}
          onClose={() => setShowEdit(false)}
          onSaved={() => { setShowEdit(false); fetchProject(); }}
        />
      )}

      {/* Delete confirm */}
      {showDelete && (
        <DeleteConfirmModal
          projectName={project.name}
          projectId={project.id}
          onClose={() => setShowDelete(false)}
        />
      )}
    </div>
  );
}

function NewListModal({
  projectId,
  currentCount,
  onClose,
  onStarted,
}: {
  projectId: number;
  currentCount: number;
  onClose: () => void;
  onStarted: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) { setError("Please choose a CSV file."); return; }
    setError(""); setLoading(true);
    try {
      // Step 1: replace wallet list
      const fd = new FormData();
      fd.append("file", file);
      const putRes = await fetch(`/api/projects/${projectId}`, { method: "PUT", body: fd });
      const putData = await putRes.json();
      if (!putRes.ok) { setError(putData.detail || "Failed to upload list."); return; }

      // Step 2: start run with new list
      const runRes = await fetch(`/api/projects/${projectId}/run`, { method: "POST" });
      const runData = await runRes.json();
      if (!runRes.ok) { setError(runData.detail || "List uploaded but failed to start run."); return; }

      onStarted();
    } catch { setError("Network error."); }
    finally { setLoading(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h3 className="font-semibold text-gray-900 mb-1">Upload new wallet list</h3>
        <p className="text-sm text-gray-500 mb-4">
          Current list: <span className="font-medium text-gray-700">{currentCount.toLocaleString()} wallets</span>.
          Uploading a new CSV will replace it and immediately start a new analysis run.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input ref={fileRef} type="file" accept=".csv" className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            <button type="button" onClick={() => fileRef.current?.click()}
              className="w-full px-3 py-3 border-2 border-dashed border-gray-300 rounded-lg text-sm text-gray-600 hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50 transition-colors text-center">
              {file ? (
                <span className="text-green-700 font-medium">✓ {file.name}</span>
              ) : (
                "Click to choose CSV file…"
              )}
            </button>
            <p className="text-xs text-gray-400 mt-1">CSV must have <code>address</code> and <code>chain</code> columns.</p>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex gap-3 pt-1">
            <button type="submit" disabled={loading || !file}
              className="flex-1 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {loading ? "Uploading & starting…" : "Upload & Run"}
            </button>
            <button type="button" onClick={onClose} disabled={loading}
              className="px-4 py-2 border border-gray-300 text-gray-700 text-sm rounded-lg hover:bg-gray-50 disabled:opacity-50">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function EditProjectModal({
  project,
  onClose,
  onSaved,
}: {
  project: ProjectDetail;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description ?? "");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) { setError("Project name is required."); return; }
    setError(""); setLoading(true);
    const fd = new FormData();
    fd.append("name", name.trim());
    fd.append("description", description.trim());
    if (file) fd.append("file", file);
    try {
      const res = await fetch(`/api/projects/${project.id}`, { method: "PUT", body: fd });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || "Failed to update project."); return; }
      onSaved();
    } catch { setError("Network error."); }
    finally { setLoading(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h3 className="font-semibold text-gray-900 mb-4">Edit Project</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Name *</label>
            <input
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Replace Wallet List (optional)</label>
            <p className="text-xs text-gray-500 mb-2">Upload a new CSV to replace the current wallet list.</p>
            <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            <button type="button" onClick={() => fileRef.current?.click()}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white hover:bg-gray-50">
              {file ? `✓ ${file.name}` : "Choose CSV file…"}
            </button>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {loading ? "Saving…" : "Save Changes"}
            </button>
            <button type="button" onClick={onClose}
              className="px-4 py-2 border border-gray-300 text-gray-700 text-sm rounded-lg hover:bg-gray-50">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function DeleteConfirmModal({
  projectName,
  projectId,
  onClose,
}: {
  projectName: string;
  projectId: number;
  onClose: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleDelete() {
    setLoading(true);
    try {
      const res = await fetch(`/api/projects/${projectId}`, { method: "DELETE" });
      if (!res.ok) {
        const d = await res.json();
        setError(d.detail || "Failed to delete project.");
        return;
      }
      window.location.href = "/projects";
    } catch { setError("Network error."); }
    finally { setLoading(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h3 className="font-semibold text-gray-900 mb-2">Delete Project</h3>
        <p className="text-sm text-gray-600 mb-4">
          Are you sure you want to delete <span className="font-medium">{projectName}</span>? This will permanently remove the project and all its run history. This action cannot be undone.
        </p>
        {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
        <div className="flex gap-3">
          <button
            onClick={handleDelete}
            disabled={loading}
            className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {loading ? "Deleting…" : "Yes, Delete"}
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 text-gray-700 text-sm rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
