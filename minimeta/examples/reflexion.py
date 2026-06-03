# minimeta/examples/reflexion.py
import asyncio
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from minimeta.llm import LLM

TASK = ("Write parse_duration(s) -> int (total seconds). Units: h, m, s, "
        "combinable in order, e.g. '1h30m'. MUST satisfy exactly: "
        "'1h30m'->5400, '45m'->2700, '2h'->7200, '90s'->90, '120'->120 (bare int = seconds). "
        "Invalid input raises ValueError. Do NOT handle negatives or fractions.")

MAX_ITERS = 3

writer = LLM(system_prompt=(

    """Your task is to write a python funcion for given prompt. you may get a critique on your code once you complete it, if so, address every point"""
))
critic = LLM(system_prompt=(

    """You are given a task that lists concrete example inputs and their expected outputs. Trace the function on each example. If it returns the expected value for all of them and raises ValueError on clearly invalid input, reply with EXACTLY APPROVED and nothing else. Otherwise, list ONLY the specific listed examples it gets wrong. Do not invent requirements beyond the task. Do not comment on style.
      """
))


class ReflexState(TypedDict):
    task: str
    draft: str
    critique: str
    iterations: int


async def generate(state: ReflexState) -> dict:
    # TODO 1: if state["critique"] is empty -> first draft from the task.
    #         else -> revise: feed task + current draft + critique to `writer`.
    #         return {"draft": <code>}
    code = await writer.aask(f"Task: {state['task']}\n\nDraft:\n{state['draft']}\n\nCritique:\n{state['critique']}\n\nWrite a revised version of the code that addresses the critique and task")
    return {"draft": code}


async def reflect(state: ReflexState) -> dict:
    # TODO 2: ask `critic` to review state["draft"] against state["task"].
    #         return {"critique": <text>, "iterations": state["iterations"] + 1}
    critique = await critic.aask(f"Task: {state['task']}\n\nDraft:\n{state['draft']}")
    return {"critique": critique, "iterations": state["iterations"] + 1}


def should_continue(state: ReflexState) -> str:
    # TODO 3: stop (END) if the critique is APPROVED or we've hit MAX_ITERS;
    #         otherwise loop back to "generate".
    if state["critique"].strip().strip('"').upper().startswith("APPROVED") or state["iterations"] >= MAX_ITERS:
        return END
    else:
        return "generate"


def build():
    b = StateGraph(ReflexState)
    # TODO 4: add nodes generate, reflect
    # TODO 5: edges START -> generate -> reflect, then conditional from reflect
    b.add_node("generate", generate)
    b.add_node("reflect", reflect)
    b.add_edge(START, "generate")
    b.add_edge("generate", "reflect")
    b.add_conditional_edges("reflect", should_continue)
    return b.compile()


if __name__ == "__main__":
    final = asyncio.run(build().ainvoke(
        {"task": TASK, "draft": "", "critique": "", "iterations": 0}
    ))
    print("=== ITERATIONS ===", final["iterations"])
    print("=== FINAL CRITIQUE ===\n", final["critique"])
    print("=== FINAL DRAFT ===\n", final["draft"])
