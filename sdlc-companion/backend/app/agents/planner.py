"""Planner (P06). Decomposes the spec into epics/tasks/estimates/dependencies."""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.drafts import PlannerOutput
from app.engines.rendering import render_type
from app.orchestrator.types import AgentContext, AgentResult
from app.schemas import DocumentType, EdgeType, Task

ROLE = (
    "You are a Planner. You decompose spec components into epics and tasks with "
    "estimates and dependencies. Every component must map to at least one task "
    "(linked_spec), every task needs an estimate, and dependencies (depends_on) "
    "must form an acyclic graph."
)


class Planner(BaseAgent):
    name = "planner"
    writes = DocumentType.TASK
    stage = 5

    def handle(self, ctx: AgentContext) -> AgentResult:
        specs = render_type(ctx.repo, DocumentType.SPEC_COMPONENT)
        tasks = render_type(ctx.repo, DocumentType.TASK)
        prompt = (
            f"User message:\n{ctx.message}\n\n"
            f"Spec components:\n{specs}\n\nExisting tasks:\n{tasks}\n\n"
            "Create tasks. Cite linked_spec (SPEC-ids); add estimates and depends_on (TASK-ids)."
        )
        out = self._generate(PlannerOutput, prompt, self._system(ROLE, ctx.project_brief))

        written: list[str] = []
        for d in out.tasks:
            payload = dict(
                title=d.title, epic=d.epic, estimate=d.estimate,
                depends_on=d.depends_on, linked_spec=d.linked_spec,
            )
            existing = ctx.repo.get_optional(d.id) if d.id else None
            if existing is not None:  # a set-but-unknown id (LLM hallucination) becomes a new node
                saved = ctx.repo.upsert(existing.model_copy(update=payload), agent=self.name)
            else:
                saved = ctx.repo.upsert(Task(**payload), agent=self.name)
            for sid in d.linked_spec:
                if ctx.repo.get_optional(sid):
                    ctx.repo.link(saved.id, sid, EdgeType.IMPLEMENTS)
            written.append(saved.id)
        return AgentResult(reply=out.reply, written_ids=written)
