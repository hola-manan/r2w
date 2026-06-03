# minimeta/examples/software_company.py
import asyncio
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from minimeta.llm import LLM

IDEA = ("A command-line to-do list app: add, list, complete, and delete tasks, "
        "persisted to a JSON file.")

pm_llm = LLM(system_prompt=(
    "You are a Product Manager. Given a product idea, write a concise PRD: "
    "goals, user stories, and functional requirements. Markdown. Do NOT write code."
))
architect_llm = LLM(system_prompt=(
    "You are a Software Architect. Given an idea and its PRD, design the solution: "
    "the file/module layout, key functions/classes with their signatures, and the data "
    "model. Markdown. Describe the structure; do NOT write full implementations."
))
engineer_llm = LLM(system_prompt=(
    "You are an Engineer. Given a design, implement it as a single, complete, runnable "
    "Python file. Output ONLY the code, in one ```python code block."
))


class ProjectState(TypedDict):
    idea: str
    prd: str
    design: str
    code: str


async def product_manager(state: ProjectState) -> dict:
    # TODO 1: ask pm_llm using state["idea"]; return {"prd": <reply>}
    reply = await pm_llm.aask(state["idea"])
    return {"prd": reply}


async def architect(state: ProjectState) -> dict:
    # TODO 2: ask architect_llm using BOTH state["idea"] and state["prd"]
    #         (build a prompt that includes the PRD); return {"design": <reply>}
    prompt = f"idea: {state['idea']}\n\nprd: {state['prd']}\n\nNow design the solution."
    reply = await architect_llm.aask(prompt)
    return {"design": reply}


async def engineer(state: ProjectState) -> dict:
    # TODO 3: ask engineer_llm using state["design"]; return {"code": <reply>}
    reply = await engineer_llm.aask(state["design"])
    return {"code": reply}


def build():
    b = StateGraph(ProjectState)
    # TODO 4: add the three nodes
    # TODO 5: wire START -> product_manager -> architect -> engineer -> END
    b.add_node("product_manager", product_manager)
    b.add_node("architect", architect)
    b.add_node("engineer", engineer)
    b.add_edge(START, "product_manager")
    b.add_edge("product_manager", "architect")
    b.add_edge("architect", "engineer")
    b.add_edge("engineer", END)
    return b.compile()


if __name__ == "__main__":
    final = asyncio.run(build().ainvoke(
        {"idea": IDEA, "prd": "", "design": "", "code": ""}
    ))
    print("\n===== PRD =====\n",    final["prd"])
    print("\n===== DESIGN =====\n", final["design"])
    print("\n===== CODE =====\n",   final["code"])
