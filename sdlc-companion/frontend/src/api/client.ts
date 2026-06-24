// Typed REST client over the P07 backend (P08).
import type {
  Artifact,
  ConfirmResult,
  GraphData,
  Profile,
  ProjectSummary,
  Scorecard,
  TurnResponse,
} from "./types";

export const API_BASE =
  (import.meta.env.VITE_API_BASE as string) || "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error((detail as any).detail || `${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listProfiles: () => req<Profile[]>("/profiles"),
  listProjects: () => req<ProjectSummary[]>("/projects"),
  getProject: (id: string) => req<ProjectSummary>(`/projects/${id}`),
  createProject: (name: string, profile_id: string) =>
    req<ProjectSummary>("/projects", {
      method: "POST",
      body: JSON.stringify({ name, profile_id }),
    }),

  listArtifacts: (id: string, opts?: { stage?: number; type?: string }) => {
    const q = new URLSearchParams();
    if (opts?.stage) q.set("stage", String(opts.stage));
    if (opts?.type) q.set("type", opts.type);
    const qs = q.toString();
    return req<Artifact[]>(`/projects/${id}/artifacts${qs ? `?${qs}` : ""}`);
  },
  getGraph: (id: string) => req<GraphData>(`/projects/${id}/graph`),

  readiness: (id: string, stage: number) =>
    req<Scorecard>(`/projects/${id}/readiness/${stage}`),
  advance: (id: string) =>
    req<ConfirmResult>(`/projects/${id}/advance`, { method: "POST" }),
  reopen: (id: string, stage: number) =>
    req<ProjectSummary>(`/projects/${id}/reopen/${stage}`, { method: "POST" }),

  message: (id: string, message: string, persona: string) =>
    req<TurnResponse>(`/projects/${id}/message`, {
      method: "POST",
      body: JSON.stringify({ message, persona }),
    }),
  challenge: (id: string, adr_id: string, objection: string) =>
    req<TurnResponse>(`/projects/${id}/challenge`, {
      method: "POST",
      body: JSON.stringify({ adr_id, objection }),
    }),

  acceptPatch: (
    id: string,
    target_id: string,
    target_type: string,
    change: Record<string, unknown>,
  ) =>
    req<Artifact>(`/projects/${id}/impact/accept`, {
      method: "POST",
      body: JSON.stringify({ target_id, target_type, change }),
    }),
  dismiss: (id: string, node_id: string, reason: string) =>
    req<{ dismissed: boolean }>(`/projects/${id}/impact/dismiss`, {
      method: "POST",
      body: JSON.stringify({ node_id, reason }),
    }),
};
