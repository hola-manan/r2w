// Shared stage logic (P09): load artifacts + readiness, send messages, advance/reopen.
import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type {
  Artifact,
  Attachment,
  ImpactItem,
  ImpactReport,
  Scorecard,
  TurnResponse,
} from "../api/types";
import type { ChatMessage } from "../components/Chat";
import type { OpenQuestion } from "../components/QuestionBoxes";

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
  // Review comments queued on artifacts (node id -> comment), submitted as a batch.
  const [pendingComments, setPendingComments] = useState<Record<string, string>>({});

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
    setPendingComments({});
    refresh();
  }, [refresh]);

  // Push a user-log entry, run a turn-producing call, and fold the response back
  // into stage state. Shared by both free-text sends and batch comment submits.
  const runTurn = useCallback(
    async (userEntry: ChatMessage, call: () => Promise<TurnResponse>): Promise<boolean> => {
      setBusy(true);
      setError("");
      setMessages((m) => [...m, userEntry]);
      try {
        const turn = await call();
        if (turn.reply) setMessages((m) => [...m, { role: "agent", content: turn.reply }]);
        setScorecard(turn.scorecard);
        setEscalation(turn.escalation);
        setImpact(turn.impact);
        await refresh();
        return true;
      } catch (e) {
        setError(String(e));
        setMessages((m) => [...m, { role: "agent", content: `⚠ ${e}` }]);
        return false;
      } finally {
        setBusy(false);
      }
    },
    [refresh],
  );

  const send = useCallback(
    async (text: string, attachments: Attachment[] = []) => {
      // Show only the typed text + attachment chips in the log, but fold the
      // extracted document text into the message the agent actually receives.
      const outgoing = [
        text,
        ...attachments.map((a) => `\n\n[Attached document: ${a.filename}]\n${a.text}`),
      ].join("");
      await runTurn(
        { role: "user", content: text, attachments: attachments.map((a) => a.filename) },
        () => api.message(projectId, outgoing, PERSONA_BY_STAGE[stage]),
      );
    },
    [projectId, stage, runTurn],
  );

  const setComment = useCallback((nodeId: string, text: string) => {
    setPendingComments((c) => {
      const next = { ...c };
      if (text.trim() === "") delete next[nodeId];
      else next[nodeId] = text;
      return next;
    });
  }, []);

  const clearComments = useCallback(() => setPendingComments({}), []);

  const submitComments = useCallback(async () => {
    const items = Object.entries(pendingComments)
      .map(([node_id, comment]) => ({ node_id, comment: comment.trim() }))
      .filter((c) => c.comment);
    if (items.length === 0) return;
    const summary =
      "Comments submitted:\n" + items.map((c) => `• ${c.node_id}: ${c.comment}`).join("\n");
    const ok = await runTurn(
      { role: "user", content: summary },
      () => api.comments(projectId, items, PERSONA_BY_STAGE[stage]),
    );
    if (ok) setPendingComments({});
  }, [projectId, stage, runTurn, pendingComments]);

  // Reconcile one impact item: drop it from the panel and fold in any follow-up
  // pass returned by accepting a patch (deduped by node id; the follow-up wins).
  const resolveImpact = useCallback(
    (resolvedId: string, followUp?: ImpactReport | null) => {
      setImpact((cur) => {
        const byId = new Map<string, ImpactItem>();
        for (const it of cur?.items ?? []) {
          if (it.node_id !== resolvedId) byId.set(it.node_id, it);
        }
        for (const it of followUp?.items ?? []) byId.set(it.node_id, it);
        const items = [...byId.values()];
        if (items.length === 0) return null;
        return { changed: followUp?.changed ?? cur?.changed ?? [], items };
      });
    },
    [],
  );

  // Open follow-up questions surfaced by the readiness scorecard, one box each.
  const openQuestions: OpenQuestion[] = (scorecard?.dimensions ?? [])
    .filter((d) => d.followup_question)
    .map((d) => ({ key: d.key, name: d.name, question: d.followup_question as string }));

  return {
    artifacts, scorecard, messages, escalation, impact, busy, error, openQuestions,
    pendingComments, commentCount: Object.keys(pendingComments).length,
    setComment, clearComments, submitComments,
    setImpact, resolveImpact, refresh, send,
  };
}
