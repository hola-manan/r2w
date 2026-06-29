import type { Artifact, ProjectSummary } from "../api/types";
import { Chat } from "../components/Chat";
import { Scorecard } from "../components/Scorecard";
import { SplitView } from "../components/SplitView";
import { AdvanceBar } from "../components/AdvanceBar";
import { LinkChips } from "../components/LinkChips";
import { CommentBar } from "../components/CommentBar";
import { CommentBox } from "../components/CommentBox";
import { useStage } from "./useStage";

function groupByEpic(tasks: Artifact[]): Record<string, Artifact[]> {
  const out: Record<string, Artifact[]> = {};
  for (const t of tasks) {
    const epic = (t.epic as string) || "Backlog";
    (out[epic] ||= []).push(t);
  }
  return out;
}

export default function Tasks({
  project,
  onChanged,
}: {
  project: ProjectSummary;
  onChanged: () => void;
}) {
  const s = useStage(project.id, 5);
  const groups = groupByEpic(s.artifacts);
  return (
    <SplitView
      left={
        <Chat
          projectId={project.id}
          questions={s.openQuestions}
          messages={s.messages}
          onSend={s.send}
          busy={s.busy}
          placeholder="Ask the Planner to break the spec into epics, tasks, estimates, and dependencies."
        />
      }
      right={
        <div className="space-y-4">
          <Scorecard card={s.scorecard} />
          <AdvanceBar
            projectId={project.id}
            stage={5}
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
          <div className="space-y-4">
            {Object.entries(groups).map(([epic, tasks]) => (
              <div key={epic}>
                <h3 className="text-sm font-medium text-slate-300 mb-2">{epic}</h3>
                <div className="grid sm:grid-cols-2 gap-2">
                  {tasks.map((t) => (
                    <div key={t.id} className="card">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs text-accent">{t.id}</span>
                        {t.estimate ? (
                          <span className="chip border-line text-slate-400">
                            {String(t.estimate)}
                          </span>
                        ) : null}
                      </div>
                      <p className="text-sm text-slate-100 mt-1">{String(t.title)}</p>
                      {Array.isArray(t.depends_on) && t.depends_on.length > 0 && (
                        <p className="text-xs text-slate-500 mt-1">
                          depends on: {(t.depends_on as string[]).join(", ")}
                        </p>
                      )}
                      <LinkChips out={t.links_out} />
                      <CommentBox
                        value={s.pendingComments[t.id] ?? ""}
                        onChange={(text) => s.setComment(t.id, text)}
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      }
    />
  );
}
