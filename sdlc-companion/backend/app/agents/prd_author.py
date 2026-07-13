"""PRD Author (P06). Drafts PRD items with full traceability to requirements."""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.drafts import PRDAuthorOutput
from app.engines.rendering import render_type
from app.orchestrator.types import AgentContext, AgentResult
from app.schemas import DocumentType, EdgeType, PRDItem

ROLE = (
    "You are a PRD Author. You turn requirements into PRD items with concrete, "
    "testable acceptance criteria and sensible priorities (must/should/could/wont). "
    "Every PRD item MUST link at least one requirement (linked_requirements), and "
    "every requirement should be covered by at least one item."
)


class PRDAuthor(BaseAgent):
    name = "prd_author"
    writes = DocumentType.PRD_ITEM
    stage = 2

    def handle(self, ctx: AgentContext) -> AgentResult:
        reqs = render_type(ctx.repo, DocumentType.REQUIREMENT)
        prds = render_type(ctx.repo, DocumentType.PRD_ITEM)
        prompt = (
            f"User message:\n{ctx.message}\n\n"
            f"Requirements:\n{reqs}\n\n"
            f"Existing PRD items:\n{prds}\n\n"
            "Draft or refine PRD items. Each must cite linked_requirements (REQ-ids)."
        )
        out = self._generate(PRDAuthorOutput, prompt, self._system(ROLE, ctx.project_brief))

        written: list[str] = []
        for d in out.items:
            payload = dict(
                title=d.title, description=d.description,
                acceptance_criteria=d.acceptance_criteria, priority=_priority(d.priority),
                linked_requirements=d.linked_requirements,
            )
            existing = ctx.repo.get_optional(d.id) if d.id else None
            if existing is not None:  # a set-but-unknown id (LLM hallucination) becomes a new node
                saved = ctx.repo.upsert(existing.model_copy(update=payload), agent=self.name)
            else:
                saved = ctx.repo.upsert(PRDItem(**payload), agent=self.name)
            for req_id in d.linked_requirements:
                if ctx.repo.get_optional(req_id):
                    ctx.repo.link(saved.id, req_id, EdgeType.DERIVES_FROM)
            written.append(saved.id)
        return AgentResult(reply=out.reply, written_ids=written)


def _priority(value: str) -> str:
    value = (value or "should").lower()
    return value if value in {"must", "should", "could", "wont"} else "should"
