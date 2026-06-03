from typing import Annotated, TypedDict
from operator import add
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    value: int                       # overwritten each time it's returned
    log: Annotated[list[str], add]   # accumulated (reducer = list concat)

def double(state: State) -> dict:
    # TODO 1: return a partial update that doubles state["value"]
    #         and appends a note to "log", e.g. f"doubled to {...}"
    return {"value": state["value"] * 2, "log": [f"doubled to {state['value'] * 2}"]}


def add_ten(state: State) -> dict:
    # TODO 2: return a partial update that adds 10 to state["value"]
    #         and appends a note to "log"
    return {"value": state["value"] + 10, "log": [f"added 10 --> {state['value'] + 10}"]}


def build():
    builder = StateGraph(State)
    # TODO 3: add both functions as nodes (builder.add_node("double", double), ...)
    builder.add_node("double", double)
    builder.add_node("add_ten", add_ten)
    # TODO 4: wire edges: START -> double -> add_ten -> END
    builder.add_edge(START, "double")
    builder.add_edge("double", "add_ten")
    builder.add_edge("add_ten", END)
    return builder.compile()


if __name__ == "__main__":
    graph = build()
    result = graph.invoke({"value": 3, "log": []})
    print(result)
