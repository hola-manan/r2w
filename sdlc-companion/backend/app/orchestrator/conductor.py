"""Conductor (P05 contract). Design doc §15.2.

Routes messages to the active stage's agent, invokes the Readiness Engine on
demand and the Impact Analyzer after confirmed edits/reopens, manages gates and
needs-review propagation. It invokes the engines (P04) — it does not contain
rubric or impact logic — and it never writes artifacts itself (agents do).
"""
from __future__ import annotations

from pydantic import BaseModel

from app.engines import ConsistencyChecker, ImpactAnalyzer, ImpactReport, ReadinessEngine, Scorecard
from app.graph import GraphRepository
from app.orchestrator.blackboard import ProposedPatch, apply_patch
from app.orchestrator.brief import update_brief
from app.orchestrator.state import (
    STAGE_OF_TYPE,
    TYPE_OF_STAGE,
    Message,
    ProjectState,
)
from app.orchestrator.state_machine import advance, assert_persona, reopen
from app.orchestrator.types import Agent, AgentContext, AgentResult
from app.profile import ProfileRetriever
from app.schemas import DocumentType, GateStatus, Persona


class ConductorResponse(BaseModel):
    reply: str
    written_ids: list[str]
    scorecard: Scorecard
    escalation: dict | None = None


class ConfirmResult(BaseModel):
    scorecard: Scorecard
    advanced: bool
    new_stage: int
    blocked_by_stale: list[str] = []  # node ids holding the gate shut (design §13.5)


class Conductor:
    def __init__(
        self,
        repo: GraphRepository,
        checker: ConsistencyChecker,
        agents: dict[int, Agent],
        retriever: ProfileRetriever | None = None,
    ) -> None:
        self.repo = repo
        self.retriever = retriever
        self.agents = agents
        self.readiness = ReadinessEngine(repo, checker, retriever)
        self.impact = ImpactAnalyzer(repo, checker)

    def _profile_summary(self) -> str:
        return self.retriever.summary() if self.retriever else ""

    def handle_message(
        self, state: ProjectState, message: str, persona: Persona
    ) -> ConductorResponse:
        assert_persona(state, persona)
        stage = state.current_stage
        agent = self.agents.get(stage)
        if agent is None:
            raise KeyError(f"no agent registered for stage {stage}")

        state.thread(stage).append(Message(role="user", content=message))
        ctx = AgentContext(
            repo=self.repo,
            message=message,
            persona=persona,
            project_brief=state.project_brief,
            retriever=self.retriever,
            history=list(state.thread(stage)),
        )
        result: AgentResult = agent.handle(ctx)
        if result.reply:
            state.thread(stage).append(Message(role="agent", content=result.reply))

        update_brief(state, self.repo, self._profile_summary())
        card = self.readiness.score(stage)
        return ConductorResponse(
            reply=result.reply,
            written_ids=result.written_ids,
            scorecard=card,
            escalation=result.escalation,
        )

    def readiness_of(self, stage: int) -> Scorecard:
        return self.readiness.score(stage)

    def confirm_stage(self, state: ProjectState) -> ConfirmResult:
        stage = state.current_stage
        card = self.readiness.score(stage)
        # The gate re-locks while the stage holds unreconciled stale nodes, even if the
        # rubric passes (design §13.5). Reconciling them (accept/dismiss -> clear_stale)
        # reopens the gate.
        stale = self._stale_nodes_in_stage(stage)
        advanced = False
        if card.gate_passed and not stale:
            advance(state, True)
            advanced = True
            update_brief(state, self.repo, self._profile_summary())
        return ConfirmResult(
            scorecard=card, advanced=advanced, new_stage=state.current_stage,
            blocked_by_stale=stale,
        )

    def _stale_nodes_in_stage(self, stage: int) -> list[str]:
        doc_type = TYPE_OF_STAGE.get(stage)
        if doc_type is None:
            return []
        return [n.id for n in self.repo.list_by_type(doc_type) if n.stale]

    def reopen_stage(self, state: ProjectState, stage: int) -> None:
        reopen(state, stage)

    def run_impact(self, state: ProjectState, changed_ids: list[str]) -> ImpactReport:
        report = self.impact.analyze(changed_ids)
        # Propagate needs-review to the stages owning any flagged node.
        for item in report.items:
            owning_stage = STAGE_OF_TYPE[DocumentType(item.doc_type)]
            if state.gate_status.get(owning_stage) == GateStatus.PASSED:
                state.gate_status[owning_stage] = GateStatus.NEEDS_REVIEW
        return report

    def apply_impact_patch(self, patch: ProposedPatch):
        owner = self.agents_owner_name(patch.target_type)
        return apply_patch(self.repo, patch, owner)

    def agents_owner_name(self, target_type: DocumentType) -> str:
        from app.orchestrator.blackboard import OWNER

        return OWNER[target_type]
