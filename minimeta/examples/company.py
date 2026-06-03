# minimeta/examples/company.py
import asyncio, json, os, re, subprocess, sys
from operator import add
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from minimeta.llm import LLM

WORKDIR = os.path.join(os.path.dirname(__file__), "_company_output")
os.makedirs(WORKDIR, exist_ok=True)
WORKERS = ["product_manager", "architect", "engineer", "qa"]
MAX_STEPS = 10

supervisor_llm = LLM(system_prompt=(
    """manage workers product_manager, architect, engineer, qa.
      Typical flow: PM -> architect -> engineer -> qa. Never pick a worker whose
      inputs don't exist yet. If qa reports FAIL, route back to engineer to fix.
      FINISH only when qa reports PASS. Reply ONLY JSON: {"next": "<worker|FINISH>"}."""
))
pm_llm        = LLM(system_prompt="You are a Product Manager. Write a short PRD. Markdown, no code.")
architect_llm = LLM(system_prompt="You are an Architect. Given the PRD, give a brief module/function design. No full code.")
engineer_llm  = LLM(system_prompt=(
    """Engineer. Given the design (and any QA failure to fix), output ONE
      complete runnable python file in a ```python block. you MUST be non-interactive:
      no input(). Include `if __name__ == '__main__':` with assert-based self-tests
      that verify the core behavior. If given a QA error, fix it."""
))
WORKER_LLMS = {"product_manager": pm_llm, "architect": architect_llm, "engineer": engineer_llm}


class TeamState(TypedDict):
    task: str
    transcript: Annotated[list[str], add]
    next: str


async def supervisor(state):
    prompt = f"TASK: {state['task']}\n\nWork so far:\n" + "\n\n".join(state["transcript"]) + "\n\nWho acts next?"
    raw = await supervisor_llm.aask(prompt, json_mode=True)
    return {"next": json.loads(raw)["next"]}


def route(state):
    nxt = state["next"].strip()
    if nxt.upper().startswith("FINISH") or len(state["transcript"]) >= MAX_STEPS:
        return END
    return nxt if nxt in WORKERS else END 


async def _llm_worker(state, name):
    reply = await WORKER_LLMS[name].aask(
        f"TASK: {state['task']}\n\nWork so far:\n" + "\n\n".join(state["transcript"]))
    return {"transcript": [f"{name.upper()}: {reply}"]}

async def product_manager(state): return await _llm_worker(state, "product_manager")
async def architect(state):       return await _llm_worker(state, "architect")

async def engineer(state):
    reply = await engineer_llm.aask(
        f"TASK: {state['task']}\n\nWork so far:\n" + "\n\n".join(state["transcript"]))
    # TODO 1: extract the ```python ...``` block from reply (regex), fall back to reply.
    #idk how to do it
    # TODO 2: write it to os.path.join(WORKDIR, "solution.py") with encoding="utf-8".
    # TODO 3: return {"transcript": [f"ENGINEER: wrote solution.py\n{code}"]}
    m = re.search(r"```python\s*\n(.*?)```", reply, re.DOTALL)
    code = m.group(1) if m else reply
    path = os.path.join(WORKDIR, "solution.py")                 
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    return {"transcript": [f"ENGINEER: wrote solution.py\n{code}"]} 



def qa(state):   # sync, NO llm — just runs the file
    path = os.path.join(WORKDIR, "solution.py")
    result = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=100)
    # TODO 4: subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=30)
    ok = "PASS" if (result.returncode == 0) else "FAIL"
    return {"transcript": [f"QA: {ok}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"]}
    
    # TODO 5: ok = (returncode == 0);  build "QA: PASS/FAIL\n<stdout+stderr>"
    # TODO 6: return {"transcript": [that string]}


def build():
    b = StateGraph(TeamState)
    b.add_node("supervisor", supervisor)
    for w in WORKERS:
        b.add_node(w, globals()[w])
    b.add_edge(START, "supervisor")
    b.add_conditional_edges("supervisor", route)
    for w in WORKERS:
        b.add_edge(w, "supervisor")
    return b.compile() #where is qa???


if __name__ == "__main__":
    final = asyncio.run(build().ainvoke(
        {"task": "A function tip_total(bill, tip_percent) -> float returning bill plus tip.",
         "transcript": [], "next": ""}
    ))
    print("\n\n".join(final["transcript"]))
    print("\n>>> project written to:", WORKDIR)
