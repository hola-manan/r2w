import type { ProjectSummary } from "../api/types";
import { ArtifactCard } from "../components/ArtifactCard";
import { Chat } from "../components/Chat";
import { Scorecard } from "../components/Scorecard";
import { SplitView } from "../components/SplitView";
import { AdvanceBar } from "../components/AdvanceBar";
import { useStage } from "./useStage";

export default function Prd({
  project,
  onChanged,
}: {
  project: ProjectSummary;
  onChanged: () => void;
}) {
  const s = useStage(project.id, 2);
  return (
    <SplitView
      left={
        <Chat
          projectId={project.id}
          questions={s.openQuestions}
          messages={s.messages}
          onSend={s.send}
          busy={s.busy}
          placeholder="Ask the PRD Author to draft or refine PRD items. Each item links its source requirements."
        />
      }
      right={
        <div className="space-y-4">
          <Scorecard card={s.scorecard} />
          <AdvanceBar
            projectId={project.id}
            stage={2}
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
