import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Scorecard } from "../api/types";

// The headline control: Advance is disabled until the stage gate passes.
export function AdvanceBar({
  projectId,
  stage,
  scorecard,
  onChanged,
}: {
  projectId: string;
  stage: number;
  scorecard: Scorecard | null;
  onChanged: () => void;
}) {
  const nav = useNavigate();
  const [busy, setBusy] = useState(false);
  const passed = scorecard?.gate_passed ?? false;

  const advance = async () => {
    setBusy(true);
    try {
      const res = await api.advance(projectId);
      onChanged();
      if (res.advanced) nav(`/project/${projectId}/stage/${res.new_stage}`);
    } finally {
      setBusy(false);
    }
  };

  const reopen = async () => {
    setBusy(true);
    try {
      await api.reopen(projectId, stage);
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex items-center justify-between border-t border-line pt-3">
      <span className="text-xs text-slate-500">
        {passed
          ? "Gate is open — you can advance."
          : "Gate is locked until hard dimensions are green."}
      </span>
      <div className="flex gap-2">
        {stage > 1 && (
          <button className="btn" onClick={reopen} disabled={busy}>
            Reopen
          </button>
        )}
        <button className="btn btn-primary" onClick={advance} disabled={!passed || busy}>
          Advance →
        </button>
      </div>
    </div>
  );
}
