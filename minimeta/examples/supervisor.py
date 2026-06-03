# minimeta/examples/supervisor.py
import asyncio
import json
from operator import add
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from minimeta.llm import LLM

WORKERS = ["product_manager", "architect", "engineer"]
MAX_STEPS = 8   # safety fence (you know why: an LLM router could loop forever)

supervisor_llm = LLM(system_prompt=(
    """You manage these workers: product_manager, architect, engineer.
      Given the task and the work done so far, decide who should act NEXT to move a
      software project forward, or "FINISH" when there is working code and nothing
      useful remains. Reply with ONLY JSON: {"next": "<worker name or FINISH>"}."""
))
pm_llm        = LLM(system_prompt="You are a Product Manager. Write a short PRD. Markdown, no code.")
architect_llm = LLM(system_prompt="You are an Architect. Given the PRD, give the module/function design. No full code.")
engineer_llm  = LLM(system_prompt="You are an Engineer. Given the design, write the complete code in one ```python block.")

WORKER_LLMS = {"product_manager": pm_llm, "architect": architect_llm, "engineer": engineer_llm}


class TeamState(TypedDict):
    task: str
    transcript: Annotated[list[str], add]
    next: str


async def supervisor(state: TeamState) -> dict:
    # TODO 1: build a prompt = task + the transcript so far + "Who acts next?"
    prompt = f"TASK: {state['task']}\n\nWork so far:\n" + "\n\n".join(state["transcript"]) + "\n\nWho acts next? Reply with ONLY JSON: {{\"next\": \"<worker name or FINISH>\"}}."
    # TODO 2: raw = await supervisor_llm.aask(prompt, json_mode=True)
    raw = await supervisor_llm.aask(prompt, json_mode=True)
    # TODO 3: return {"next": json.loads(raw)["next"]}
    return {"next": json.loads(raw)["next"]}


def route(state: TeamState) -> str:
    # TODO 4: if state["next"] == "FINISH" (or we've exceeded MAX_STEPS) -> END,
    #         else return state["next"]  (the chosen worker node name)
    #         (hint: len(state["transcript"]) is a decent step counter)
    if state["next"] == "FINISH" or len(state["transcript"]) >= MAX_STEPS:
        return END
    else:
        return state["next"]
    ...


async def run_worker(state: TeamState, name: str) -> dict:
    # helper: ask that worker, append its output to the transcript
    reply = await WORKER_LLMS[name].aask(
        f"TASK: {state['task']}\n\nWork so far:\n" + "\n\n".join(state["transcript"])
    )
    return {"transcript": [f"{name.upper()}: {reply}"]} #why do u use []? what if i use only one string?


# one node per worker (they all reuse run_worker)
async def product_manager(state): return await run_worker(state, "product_manager")
async def architect(state):       return await run_worker(state, "architect")
async def engineer(state):        return await run_worker(state, "engineer")


def build():
    b = StateGraph(TeamState)
    b.add_node("supervisor", supervisor)
    for w in WORKERS:
        b.add_node(w, globals()[w])#why this instead of connecting them to the supervisor with condional? or using the workers as tools?
    b.add_edge(START, "supervisor")
    # TODO 5: conditional edge from "supervisor" using route
    #         (so the supervisor's decision picks the next node)
    b.add_conditional_edges("supervisor", route)
    # TODO 6: every worker routes BACK to "supervisor" after acting
    #         (add_edge(w, "supervisor") for each w)
    for w in WORKERS:
        b.add_edge(w, "supervisor")
    return b.compile()


if __name__ == "__main__":
    final = asyncio.run(build().ainvoke(
        {"task": "Build a CLI tip calculator (bill + tip% -> total).",
         "transcript": [], "next": ""}
    ))
    print("\n\n".join(final["transcript"]))
