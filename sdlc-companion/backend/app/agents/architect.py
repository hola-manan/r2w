"""Architect / spec co-editor (P06).

Writes spec components, links them to PRD items and ADRs. Never edits ADR/PRD
directly — it emits proposed_adr_changes (ProposedPatch) for the owning agent
to apply after impact review (blackboard rule, §15.3).
"""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.drafts import ArchitectOutput
from app.engines.rendering import render_type
from app.orchestrator.blackboard import ProposedPatch
from app.orchestrator.types import AgentContext, AgentResult
from app.schemas import DocumentType, EdgeType, SpecComponent

ROLE = (
    "You are a Tech Architect co-editing a technical spec. You translate PRD items "
    "and ADR decisions into spec components with responsibilities, interfaces, and a "
    "data model. Each component must realize at least one PRD item (linked_prd) and "
    "reference the ADRs it depends on (tech_refs). You do NOT edit PRDs or ADRs "
    "directly; if a decision needs to change, emit a proposed_adr_change."
)


class Architect(BaseAgent):
    name = "architect"
    writes = DocumentType.SPEC_COMPONENT

    def handle(self, ctx: AgentContext) -> AgentResult:
        prds = render_type(ctx.repo, DocumentType.PRD_ITEM)
        adrs = render_type(ctx.repo, DocumentType.ADR)
        specs = render_type(ctx.repo, DocumentType.SPEC_COMPONENT)
        prompt = (
            f"User message:\n{ctx.message}\n\n"
            f"PRD items:\n{prds}\n\nADRs:\n{adrs}\n\nExisting components:\n{specs}\n\n"
            "Create or refine spec components. Cite linked_prd (PRD-ids) and tech_refs (ADR-ids)."
        )
        out = self._generate(ArchitectOutput, prompt, self._system(ROLE, ctx.project_brief))

        written: list[str] = []
        for d in out.components:
            payload = dict(
                name=d.name, responsibility=d.responsibility, tech_refs=d.tech_refs,
                interfaces=d.interfaces, data=d.data, linked_prd=d.linked_prd, risks=d.risks,
            )
            if d.id:
                node = ctx.repo.get(d.id).model_copy(update=payload)
                saved = ctx.repo.upsert(node, agent=self.name)
            else:
                saved = ctx.repo.upsert(SpecComponent(**payload), agent=self.name)
            for pid in d.linked_prd:
                if ctx.repo.get_optional(pid):
                    ctx.repo.link(saved.id, pid, EdgeType.REALIZES)
            for aid in d.tech_refs:
                if ctx.repo.get_optional(aid):
                    ctx.repo.link(saved.id, aid, EdgeType.REALIZES)
            written.append(saved.id)

        proposed = [
            ProposedPatch(
                target_id=c.target_id, target_type=DocumentType.ADR,
                change=c.change, origin_agent=self.name, reason=c.reason,
            ).model_dump(mode="json")
            for c in out.proposed_adr_changes
        ]
        escalation = {"proposed_adr_changes": proposed} if proposed else None
        return AgentResult(reply=out.reply, written_ids=written, escalation=escalation)
