import type { ProjectSummary } from "../api/types";
import { Chat } from "../components/Chat";
import { Scorecard } from "../components/Scorecard";
import { SplitView } from "../components/SplitView";
import { AdvanceBar } from "../components/AdvanceBar";
import { ArtifactCard } from "../components/ArtifactCard";
import { useStage } from "./useStage";

export default function Requirements({
  project,
  onChanged,
}: {
  project: ProjectSummary;
  onChanged: () => void;
}) {
  const s = useStage(project.id, 1);
  return (
    <SplitView
      left={
        <Chat
          projectId={project.id}
          questions={s.openQuestions}
          messages={s.messages}
          onSend={s.send}
          busy={s.busy}
          placeholder="Describe the business need in plain language. The Requirements Analyst will ask gap-closing questions."
        />
      }
      right={
        <div className="space-y-4">
          <Scorecard card={s.scorecard} />
          <AdvanceBar
            projectId={project.id}
            stage={1}
            scorecard={s.scorecard}
            onChanged={() => {
              s.refresh();
              onChanged();
            }}
          />
          <div className="space-y-2">
            {s.artifacts.map((a) => (
              <ArtifactCard key={a.id} artifact={a} />
            ))}
          </div>
        </div>
      }
    />
  );
}
