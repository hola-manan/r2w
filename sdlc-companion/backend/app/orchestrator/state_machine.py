"""State machine (P05). Forward gates + reopen -> downstream needs_review.

Design doc §15.1: forward transitions guarded by gates; reopen allowed (hybrid
model) and sets downstream needs_review; persona/stage validity enforced.
"""
from __future__ import annotations

from app.orchestrator.state import STAGES, ProjectState, persona_for_stage
from app.schemas import GateStatus, Persona


class GateNotPassed(Exception):
    pass


class PersonaViolation(Exception):
    pass


def new_state(project_id: str) -> ProjectState:
    state = ProjectState(project_id=project_id)
    state.gate_status = {s: GateStatus.LOCKED for s in STAGES}
    state.current_stage = 1
    state.persona = persona_for_stage(1)
    return state


def assert_persona(state: ProjectState, persona: Persona) -> None:
    required = persona_for_stage(state.current_stage)
    if persona != required:
        raise PersonaViolation(
            f"Stage {state.current_stage} requires persona '{required.value}', "
            f"got '{persona.value}'."
        )


def advance(state: ProjectState, gate_passed: bool) -> ProjectState:
    if not gate_passed:
        raise GateNotPassed(f"Stage {state.current_stage} gate is not passed.")
    state.gate_status[state.current_stage] = GateStatus.PASSED
    if state.current_stage < STAGES[-1]:
        state.current_stage += 1
        state.persona = persona_for_stage(state.current_stage)
    return state


def reopen(state: ProjectState, stage: int) -> ProjectState:
    if stage not in STAGES:
        raise ValueError(f"invalid stage {stage}")
    state.current_stage = stage
    state.persona = persona_for_stage(stage)
    state.gate_status[stage] = GateStatus.LOCKED
    # Everything downstream that was passed now needs review.
    for s in STAGES:
        if s > stage and state.gate_status.get(s) == GateStatus.PASSED:
            state.gate_status[s] = GateStatus.NEEDS_REVIEW
    return state
