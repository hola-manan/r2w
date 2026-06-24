import { useNavigate } from "react-router-dom";
import type { GateStatus, ProjectSummary } from "../api/types";
import { GateBadge } from "./Badges";

const STAGES = [1, 2, 3, 4, 5];

export function StageRail({
  project,
  active,
}: {
  project: ProjectSummary;
  active: number;
}) {
  const nav = useNavigate();
  return (
    <nav className="flex items-stretch gap-2">
      {STAGES.map((s) => {
        const status: GateStatus = project.gate_status[String(s)] ?? "locked";
        const isActive = s === active;
        return (
          <button
            key={s}
            onClick={() => nav(`/project/${project.id}/stage/${s}`)}
            className={`flex-1 text-left rounded-lg border px-3 py-2 transition ${
              isActive ? "border-accent bg-ink-soft" : "border-line hover:border-accent/50"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Stage {s}</span>
              <GateBadge status={status} />
            </div>
            <div className="text-sm font-medium text-slate-100">
              {project.stage_names[String(s)]}
            </div>
          </button>
        );
      })}
    </nav>
  );
}
