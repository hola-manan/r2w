# minimeta/examples/debate.py
import asyncio
from operator import add
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from minimeta.llm import LLM

TOPIC = "Should AI-written code be allowed in production without human review?"
MAX_ROUNDS = 3

# Each debater = the same wrapper with a different identity (system prompt).
pro_llm = LLM(system_prompt="You argue FOR the motion. Reply in ONE punchy paragraph. "
                            "Directly rebut the opponent's last point if there is one.")
con_llm = LLM(system_prompt="You argue AGAINST the motion. Reply in ONE punchy paragraph. "
                            "Directly rebut the opponent's last point if there is one.")


class DebateState(TypedDict):
    topic: str
    transcript: Annotated[list[str], add]   # grows each turn (reducer!)
    round: int                              # plain channel: overwritten

def _prompt(state: DebateState) -> str:
    # TODO 1: return a string containing the topic and the transcript so far
    #         (join state["transcript"] with newlines). This is the context
    #         each debater reads before replying.
    return f"topic: {state['topic']}\n" + "\n".join(state["transcript"])


async def pro(state: DebateState) -> dict:
    # TODO 2: reply = await pro_llm.aask(_prompt(state))
    #         return a delta appending f"PRO: {reply}" to transcript
    reply = await pro_llm.aask(_prompt(state))
    return {"transcript": [f"PRO: {reply}"]}


async def con(state: DebateState) -> dict:
    # TODO 3: like pro, but con_llm — AND advance the round counter
    #         return {"transcript": [f"CON: {reply}"], "round": state["round"] + 1}
    reply = await con_llm.aask(_prompt(state))
    return {"transcript": [f"CON: {reply}"], "round": state["round"] + 1}


def should_continue(state: DebateState) -> str:
    # TODO 4: return "pro" to loop for another round, else END
    if state["round"] < MAX_ROUNDS:
        return "pro"
    return END


def build():
    b = StateGraph(DebateState)
    # TODO 5: add nodes "pro" and "con"
    # TODO 6: edges: START -> pro, pro -> con
    # TODO 7: conditional edge from "con" using should_continue
    b.add_node("pro", pro)
    b.add_node("con", con)
    b.add_edge(START, "pro")
    b.add_edge("pro", "con")
    b.add_conditional_edges("con", should_continue)
    return b.compile()


if __name__ == "__main__":
    graph = build()
    final = asyncio.run(graph.ainvoke({"topic": TOPIC, "transcript": [], "round": 0}))
    print("\n\n".join(final["transcript"]))
