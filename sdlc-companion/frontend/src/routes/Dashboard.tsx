import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Profile, ProjectSummary } from "../api/types";
import { GateBadge } from "../components/Badges";

export default function Dashboard() {
  const nav = useNavigate();
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [name, setName] = useState("");
  const [profileId, setProfileId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.listProfiles().then((p) => {
      setProfiles(p);
      if (p[0]) setProfileId(p[0].id);
    }).catch((e) => setError(String(e)));
    api.listProjects().then(setProjects).catch(() => {});
  }, []);

  const create = async () => {
    if (!name.trim()) return;
    setBusy(true);
    setError("");
    try {
      const proj = await api.createProject(name.trim(), profileId);
      nav(`/project/${proj.id}/stage/1`);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      <section className="card">
        <h2 className="font-semibold text-slate-100 mb-3">New project</h2>
        {error && <p className="text-sm text-rag-red mb-2">{error}</p>}
        <div className="grid sm:grid-cols-[1fr_auto_auto] gap-3 items-end">
          <div>
            <label className="text-xs text-slate-500">Name</label>
            <input
              className="input"
              value={name}
              placeholder="e.g. Customer Feedback Portal"
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-slate-500">Company profile</label>
            <select
              className="input"
              value={profileId}
              onChange={(e) => setProfileId(e.target.value)}
            >
              {profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <button className="btn btn-primary" onClick={create} disabled={busy}>
            Start
          </button>
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Tip: run the same request against two profiles to see different,
          internally-consistent stacks.
        </p>
      </section>

      <section>
        <h2 className="font-semibold text-slate-100 mb-3">Projects</h2>
        {projects.length === 0 ? (
          <p className="text-sm text-slate-500">No projects yet.</p>
        ) : (
          <div className="grid sm:grid-cols-2 gap-3">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => nav(`/project/${p.id}/stage/${p.current_stage}`)}
                className="card text-left hover:border-accent/50"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-slate-100">{p.name}</span>
                  <GateBadge status={p.gate_status[String(p.current_stage)] ?? "locked"} />
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {p.profile_id || "no profile"} · stage {p.current_stage} (
                  {p.stage_names[String(p.current_stage)]})
                </div>
              </button>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
