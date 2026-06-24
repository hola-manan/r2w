// Shared stage logic (P09): load artifacts + readiness, send messages, advance/reopen.
import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type {
  Artifact,
  ImpactReport,
  Scorecard,
} from "../api/types";
import type { ChatMessage } from "../components/Chat";

export const TYPE_BY_STAGE: Record<number, string> = {
  1: "requirement",
  2: "prd_item",
  3: "adr",
  4: "spec_component",
  5: "task",
};

export const PERSONA_BY_STAGE: Record<number, string> = {
  1: "business_user",
  2: "business_user",
  3: "tech_architect",
  4: "tech_architect",
  5: "tech_architect",
};

export function useStage(projectId: string, stage: number) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [scorecard, setScorecard] = useState<Scorecard | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [escalation, setEscalation] = useState<Record<string, unknown> | null>(null);
  const [impact, setImpact] = useState<ImpactReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const [arts, card] = await Promise.all([
      api.listArtifacts(projectId, { type: TYPE_BY_STAGE[stage] }),
      api.readiness(projectId, stage).catch(() => null),
    ]);
    setArtifacts(arts);
    setScorecard(card);
  }, [projectId, stage]);

  useEffect(() => {
    setMessages([]);
    setEscalation(null);
    setImpact(null);
    refresh();
  }, [refresh]);

  const send = useCallback(
    async (text: string) => {
      setBusy(true);
      setError("");
      setMessages((m) => [...m, { role: "user", content: text }]);
      try {
        const turn = await api.message(projectId, text, PERSONA_BY_STAGE[stage]);
        if (turn.reply) setMessages((m) => [...m, { role: "agent", content: turn.reply }]);
        setScorecard(turn.scorecard);
        setEscalation(turn.escalation);
        setImpact(turn.impact);
        await refresh();
      } catch (e) {
        setError(String(e));
        setMessages((m) => [...m, { role: "agent", content: `⚠ ${e}` }]);
      } finally {
        setBusy(false);
      }
    },
    [projectId, stage, refresh],
  );

  return {
    artifacts, scorecard, messages, escalation, impact, busy, error,
    setImpact, refresh, send,
  };
}
