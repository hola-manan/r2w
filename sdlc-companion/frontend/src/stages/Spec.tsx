import { useState } from "react";
import { api } from "../api/client";
import type { ImpactItem, ImpactReport, ProjectSummary } from "../api/types";
import { ArtifactCard } from "../components/ArtifactCard";
import { Chat } from "../components/Chat";
import { Scorecard } from "../components/Scorecard";
import { SplitView } from "../components/SplitView";
import { AdvanceBar } from "../components/AdvanceBar";
import { CommentBar } from "../components/CommentBar";
import { useStage } from "./useStage";

function ImpactPanel({
  projectId,
  items,
  onResolved,
}: {
  projectId: string;
  items: ImpactItem[];
  onResolved: (resolvedId: string, followUp?: ImpactReport) => void;
}) {
  const [busy, setBusy] = useState(false);
  if (items.length === 0) return null;

  const accept = async (it: ImpactItem) => {
    setBusy(true);
    try {
      // Accepting opens the next pass; fold its newly-flagged neighbors into the panel.
      const res = await api.acceptPatch(projectId, it.node_id, it.doc_type, it.suggested_patch || {});
      onResolved(it.node_id, res.impact);
    } finally {
      setBusy(false);
    }
  };
  const dismiss = async (it: ImpactItem) => {
    const reason = window.prompt(`Dismiss impact on ${it.node_id} — reason?`);
    if (!reason) return;
    setBusy(true);
    try {
      await api.dismiss(projectId, it.node_id, reason);
      onResolved(it.node_id);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card border-rag-amber/50">
      <h3 className="text-rag-amber font-medium mb-2">Impact — review needed</h3>
      <ul className="space-y-2">
        {items.map((it) => (
          <li key={it.node_id} className="text-sm border-t border-line pt-2 first:border-0 first:pt-0">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-accent">{it.node_id}</span>
              <span className="chip border-rag-amber/50 text-rag-amber">{it.status}</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">{it.justification}</p>
            {it.suggested_patch && (
              <pre className="text-xs text-slate-500 mt-1 whitespace-pre-wrap">
                patch: {JSON.stringify(it.suggested_patch)}
              </pre>
            )}
            <div className="flex gap-2 mt-2">
              <button className="btn" onClick={() => accept(it)} disabled={busy}>
                Accept patch
              </button>
              <button className="btn" onClick={() => dismiss(it)} disabled={busy}>
                Dismiss
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function Spec({
  project,
  onChanged,
}: {
  project: ProjectSummary;
  onChanged: () => void;
}) {
  const s = useStage(project.id, 4);
  return (
    <SplitView
      left={
        <Chat
          projectId={project.id}
          questions={s.openQuestions}
          messages={s.messages}
          onSend={s.send}
          busy={s.busy}
          placeholder="Co-edit the tech spec with the Architect. Edits ripple — the impact panel flags stale nodes."
        />
      }
      right={
        <div className="space-y-4">
          <Scorecard card={s.scorecard} />
          <ImpactPanel
            projectId={project.id}
            items={s.impact?.items ?? []}
            onResolved={(resolvedId, followUp) => {
              s.resolveImpact(resolvedId, followUp);
              s.refresh();
              onChanged();
            }}
          />
          <AdvanceBar
            projectId={project.id}
            stage={4}
            scorecard={s.scorecard}
            onChanged={() => {
              s.refresh();
              onChanged();
            }}
          />
          <CommentBar
            count={s.commentCount}
            busy={s.busy}
            onSubmit={s.submitComments}
            onClear={s.clearComments}
          />
          <div className="space-y-2">
            {s.artifacts.map((a) => (
              <ArtifactCard
                key={a.id}
                artifact={a}
                commentValue={s.pendingComments[a.id] ?? ""}
                onCommentChange={(t) => s.setComment(a.id, t)}
              />
            ))}
          </div>
        </div>
      }
    />
  );
}
