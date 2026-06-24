"""Stack Advisor (P06). Constrained generation + ADR authoring + challenge flow.

Design doc §14: candidates come from the radar, Hold is excluded, choices are
validated against the profile, hard constraints must be satisfied, and conflicts
are escalated rather than silently violated.
"""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.drafts import ADRDraft, StackAdvisorOutput
from app.engines.rendering import render_type
from app.orchestrator.types import AgentContext, AgentResult
from app.profile import validate_choice
from app.schemas import ADR, ADROption, DocumentType, EdgeType, Ring

ROLE = (
    "You are a Stack Advisor. You decide one technology per decision point "
    "(datastore, backend runtime, frontend, auth, hosting, messaging, realtime...). "
    "You may ONLY choose technologies on the company tech radar: prefer Adopt, "
    "allow Trial only with a caveat + named Adopt fallback + risk note, never Hold. "
    "Each ADR must state its `context` (the PRD/COMP IDs that drive the decision) and "
    "cite the PRD/COMP IDs it satisfies and the radar entries used. "
    "If a need can only be met by a Hold/off-radar technology, DO NOT choose it — "
    "set `escalation` describing the conflict and the options."
)


class StackAdvisor(BaseAgent):
    name = "stack_advisor"
    writes = DocumentType.ADR

    def _prompt(self, ctx: AgentContext, extra: str = "") -> str:
        prds = render_type(ctx.repo, DocumentType.PRD_ITEM)
        profile = ctx.retriever.summary() if ctx.retriever else "(no profile)"
        return (
            f"User message:\n{ctx.message}\n\n{extra}"
            f"PRD items:\n{prds}\n\n"
            f"{profile}\n\n"
            "Produce ADRs (one per decision point) choosing only from the radar."
        )

    def handle(self, ctx: AgentContext) -> AgentResult:
        out = self._generate(
            StackAdvisorOutput, self._prompt(ctx), self._system(ROLE, ctx.project_brief)
        )
        return self._apply(ctx, out)

    def challenge(self, ctx: AgentContext, adr_id: str, objection: str) -> AgentResult:
        """Architect challenge: reopen ONLY this decision, emit a superseding ADR."""
        old = ctx.repo.get(adr_id)
        extra = (
            f"The architect challenges {adr_id} (decided '{old.decision}', chose "
            f"'{old.chosen}'). Objection: {objection}\n"
            "Re-decide ONLY this decision point with the objection folded in.\n\n"
        )
        out = self._generate(
            StackAdvisorOutput, self._prompt(ctx, extra), self._system(ROLE, ctx.project_brief)
        )
        result = self._apply(ctx, out)
        # Supersede the old ADR if a new one was written.
        new_ids = [i for i in result.written_ids]
        if new_ids:
            new_id = new_ids[0]
            old = ctx.repo.get(adr_id).model_copy(
                update={"status": "superseded", "superseded_by": new_id}
            )
            ctx.repo.upsert(old, agent=self.name)
            result.written_ids.append(adr_id)
        return result

    def _apply(self, ctx: AgentContext, out: StackAdvisorOutput) -> AgentResult:
        written: list[str] = []
        escalation = out.escalation
        for d in out.adrs:
            if ctx.retriever is not None:
                check = validate_choice(ctx.retriever, d.chosen)
                if not check.allowed:
                    escalation = escalation or {
                        "type": "radar_conflict",
                        "decision": d.decision,
                        "chosen": d.chosen,
                        "reason": check.reason,
                        "options": ["relax requirement", "off-radar exception", "rescope"],
                    }
                    continue  # never silently write a violating ADR
            adr = ctx.repo.upsert(self._to_adr(d), agent=self.name)
            for sid in d.satisfies:
                if ctx.repo.get_optional(sid):
                    ctx.repo.link(adr.id, sid, EdgeType.SATISFIES)
            written.append(adr.id)
        return AgentResult(reply=out.reply, written_ids=written, escalation=escalation)

    @staticmethod
    def _to_adr(d: ADRDraft) -> ADR:
        options = [
            ADROption(name=o.name, ring=_ring(o.ring), excluded=o.excluded, note=o.note)
            for o in d.options
        ]
        return ADR(
            decision=d.decision, chosen=d.chosen, context=d.context or list(d.satisfies),
            options=options, rationale=d.rationale,
            satisfies=d.satisfies, radar_refs=d.radar_refs, risks=d.risks,
        )


def _ring(value):
    if not value:
        return None
    try:
        return Ring(value.lower())
    except ValueError:
        return None
