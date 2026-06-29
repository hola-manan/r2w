import { useState } from "react";
import { api } from "../api/client";
import type { Artifact, ProjectSummary } from "../api/types";
import { ArtifactCard } from "../components/ArtifactCard";
import { RingBadge } from "../components/Badges";
import { Chat } from "../components/Chat";
import { CommentBar } from "../components/CommentBar";
import { Scorecard } from "../components/Scorecard";
import { SplitView } from "../components/SplitView";
import { AdvanceBar } from "../components/AdvanceBar";
import { useStage } from "./useStage";

function AdrCard({
  adr,
  projectId,
  onChanged,
  commentValue,
  onCommentChange,
}: {
  adr: Artifact;
  projectId: string;
  onChanged: () => void;
  commentValue?: string;
  onCommentChange?: (text: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const options = (adr.options as { name: string; ring?: string }[]) || [];
  const radar = (adr.radar_refs as string[]) || [];

  const challenge = async () => {
    const objection = window.prompt(`Challenge ${adr.id} — what's your objection?`);
    if (!objection) return;
    setBusy(true);
    try {
      await api.challenge(projectId, adr.id, objection);
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  return (
    <ArtifactCard artifact={adr} commentValue={commentValue} onCommentChange={onCommentChange}>
      <div className="flex flex-wrap gap-1.5 mt-2">
        {options.map((o, i) => (
          <span key={i} className="inline-flex items-center gap-1">
            <span className="text-xs text-slate-400">{o.name}</span>
            <RingBadge ring={o.ring} />
          </span>
        ))}
        {radar.map((r) => (
          <span key={r} className="chip border-accent/40 text-accent">
            radar:{r}
          </span>
        ))}
      </div>
      {adr.status === "superseded" && (
        <p className="text-xs text-rag-amber mt-1">superseded by {String(adr.superseded_by)}</p>
      )}
      {adr.status !== "superseded" && (
        <button className="btn mt-3" onClick={challenge} disabled={busy}>
          Challenge this
        </button>
      )}
    </ArtifactCard>
  );
}

function EscalationCard({ escalation }: { escalation: Record<string, unknown> }) {
  if (escalation.type === "radar_conflict") {
    const options = (escalation.options as string[]) ?? [];
    return (
      <div className="card border-rag-amber/50">
        <h3 className="text-rag-amber font-medium">Conflict — your call</h3>
        <p className="text-sm text-slate-300 mt-1">
          <span className="font-mono text-xs text-accent">{String(escalation.chosen)}</span> can't
          be used for “{String(escalation.decision)}”: {String(escalation.reason)}
        </p>
        <ul className="mt-2 flex flex-wrap gap-1.5">
          {options.map((o) => (
            <li key={o} className="chip border-line text-slate-300">
              {o}
            </li>
          ))}
        </ul>
        <p className="text-xs text-slate-500 mt-2">
          Tell the Stack Advisor which path to take in the chat.
        </p>
      </div>
    );
  }
  // Unknown escalation shape (e.g. proposed_adr_changes): show it raw.
  return (
    <div className="card border-rag-amber/50">
      <h3 className="text-rag-amber font-medium">Conflict escalation</h3>
      <pre className="text-xs text-slate-300 whitespace-pre-wrap mt-1">
        {JSON.stringify(escalation, null, 2)}
      </pre>
    </div>
  );
}

export default function Stack({
  project,
  onChanged,
}: {
  project: ProjectSummary;
  onChanged: () => void;
}) {
  const s = useStage(project.id, 3);
  return (
    <SplitView
      left={
        <Chat
          projectId={project.id}
          questions={s.openQuestions}
          messages={s.messages}
          onSend={s.send}
          busy={s.busy}
          placeholder="Ask the Stack Advisor to propose a stack. It only chooses from the radar and cites compliance."
        />
      }
      right={
        <div className="space-y-4">
          <Scorecard card={s.scorecard} />
          {s.escalation && <EscalationCard escalation={s.escalation} />}
          <AdvanceBar
            projectId={project.id}
            stage={3}
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
              <AdrCard
                key={a.id}
                adr={a}
                projectId={project.id}
                commentValue={s.pendingComments[a.id] ?? ""}
                onCommentChange={(t) => s.setComment(a.id, t)}
                onChanged={() => {
                  s.refresh();
                  onChanged();
                }}
              />
            ))}
          </div>
        </div>
      }
    />
  );
}
