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
  const [note, setNote] = useState("");
  const passed = scorecard?.gate_passed ?? false;

  const advance = async () => {
    setBusy(true);
    setNote("");
    try {
      const res = await api.advance(projectId);
      onChanged();
      if (res.advanced) {
        nav(`/project/${projectId}/stage/${res.new_stage}`);
      } else if (res.blocked_by_stale.length > 0) {
        // Gate rubric passed but stale nodes hold it shut (design §13.5).
        setNote(
          `Reconcile ${res.blocked_by_stale.length} stale item(s) in the impact panel first: ` +
            res.blocked_by_stale.join(", "),
        );
      }
    } finally {
      setBusy(false);
    }
  };

  const reopen = async () => {
    setBusy(true);
    setNote("");
    try {
      await api.reopen(projectId, stage);
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="border-t border-line pt-3">
      <div className="flex items-center justify-between">
        <span className="text-xs text-slate-500">
          {passed
            ? "Gate rubric is satisfied — you can advance once nothing needs review."
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
      {note && <p className="mt-2 text-xs text-rag-amber">{note}</p>}
    </div>
  );
}
