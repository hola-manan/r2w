"""Requirements Analyst (P06). Goal-driven elicitation toward closing rubric gaps."""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.drafts import ReqAnalystOutput
from app.engines.rendering import render_type
from app.orchestrator.types import AgentContext, AgentResult
from app.schemas import DocumentType, Requirement

ROLE = (
    "You are a Requirements Analyst. Through conversation you extract clear, "
    "testable, scoped requirements from a business user. You score against the "
    "Requirements rubric (clarity, testability, scope, completeness, feasibility, "
    "NFR coverage, success metrics) and ask ONLY gap-closing follow-up questions. "
    "Mark each requirement functional or nfr."
)


class RequirementsAnalyst(BaseAgent):
    name = "requirements_analyst"
    writes = DocumentType.REQUIREMENT

    def handle(self, ctx: AgentContext) -> AgentResult:
        existing = render_type(ctx.repo, DocumentType.REQUIREMENT)
        prompt = (
            f"User message:\n{ctx.message}\n\n"
            f"Existing requirements:\n{existing}\n\n"
            "Extract new requirements or refine existing ones (set `id` to refine). "
            "Reply conversationally and, if anything is vague, ask a gap-closing question."
        )
        out = self._generate(ReqAnalystOutput, prompt, self._system(ROLE, ctx.project_brief))

        written: list[str] = []
        for d in out.requirements:
            if d.id:
                node = ctx.repo.get(d.id)
                node = node.model_copy(
                    update={"statement": d.statement, "req_type": d.req_type,
                            "open_questions": d.open_questions}
                )
                saved = ctx.repo.upsert(node, agent=self.name)
            else:
                saved = ctx.repo.upsert(
                    Requirement(statement=d.statement, req_type=d.req_type,
                                open_questions=d.open_questions),
                    agent=self.name,
                )
            written.append(saved.id)
        return AgentResult(reply=out.reply, written_ids=written)
