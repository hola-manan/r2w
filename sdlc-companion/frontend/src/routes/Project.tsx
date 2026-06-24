import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import type { ProjectSummary } from "../api/types";
import { StageRail } from "../components/StageRail";
import Requirements from "../stages/Requirements";
import Prd from "../stages/Prd";
import Stack from "../stages/Stack";
import Spec from "../stages/Spec";
import Tasks from "../stages/Tasks";

const STAGE_COMPONENTS: Record<number, typeof Requirements> = {
  1: Requirements,
  2: Prd,
  3: Stack,
  4: Spec,
  5: Tasks,
};

export default function Project() {
  const params = useParams();
  const id = params.id!;
  const stage = Number(params.stage) || 0;
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(() => {
    api.getProject(id).then(setProject).catch((e) => setError(String(e)));
  }, [id]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (error) return <div className="p-6 text-rag-red">{error}</div>;
  if (!project) return <div className="p-6 text-slate-500">Loading…</div>;

  const active = stage || project.current_stage;
  const StageView = STAGE_COMPONENTS[active] ?? Requirements;
  const personaLabel =
    active <= 2 ? "Business User" : "Tech Architect";

  return (
    <div className="h-full flex flex-col p-4 gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-semibold text-slate-100">{project.name}</h1>
          <span className="text-xs text-slate-500">
            profile: {project.profile_id || "none"} · persona: {personaLabel}
          </span>
        </div>
      </div>
      <StageRail project={project} active={active} />
      <div className="flex-1 min-h-0">
        <StageView project={project} onChanged={refresh} />
      </div>
    </div>
  );
}
