# minimeta/examples/code_agent.py
import os
import subprocess
import sys

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

WORKDIR = os.path.join(os.path.dirname(__file__), "_agent_output")
os.makedirs(WORKDIR, exist_ok=True)


@tool
def write_file(filename: str, content: str) -> str:
    """edits a file in the current directory(provided filename and content as input) and returns a success message"""
    path = os.path.join(WORKDIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} chars to {filename}."


@tool
def run_python_file(filename: str) -> str:
    """executes a Python file(with filename as input) in the current directoryand returns its output (or errors)"""
    path = os.path.join(WORKDIR, filename)
    proc = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=30)
    return (proc.stdout + proc.stderr).strip() or "(ran, no output)"


SYSTEM_PROMPT = """
you are a Python engineer that builds programs by writing files and running them,
you MUST
RUN your code to verify it works,
FIX any errors you sees, 
and only finish once the program runs correctly.
"""


def build_agent():
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=os.environ["GEMINI_API_KEY"],
        temperature=0,
    )
    # TODO 1: agent = create_react_agent(model, tools=[write_file, run_python_file],
    #                                    prompt=SYSTEM_PROMPT)
    agent = create_react_agent(model, tools=[write_file, run_python_file], prompt=SYSTEM_PROMPT)
    # TODO 2: return agent
    return agent


if __name__ == "__main__":
    agent = build_agent()
    task = ("Create fizzbuzz.py that prints numbers 1..20, but 'Fizz' for multiples of 3, "
            "'Buzz' for multiples of 5, and 'FizzBuzz' for multiples of both. Run it to confirm.")
    result = agent.invoke({"messages": [("user", task)]})
    # print the whole conversation so you can watch the loop
    for m in result["messages"]:
        m.pretty_print()
