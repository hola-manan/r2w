# minimeta/examples/react_agent.py
import asyncio
import io
import contextlib
import json
import traceback

from minimeta.llm import LLM


# ---- TOOL (provided) -------------------------------------------------------
def run_python(code: str) -> str:
    """Execute Python code in-process; return its stdout, or the traceback."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, {})                       # local learning sandbox only — never on untrusted input
        return buf.getvalue() or "(ran OK, no output)"
    except Exception:
        return "ERROR:\n" + traceback.format_exc()


TOOLS = {"run_python": run_python}


# ---- JSON PARSER (provided) ------------------------------------------------
def parse(raw: str) -> dict:
    """Turn the model's reply into a dict, tolerating ```json fences."""
    t = raw.strip()
    if t.startswith("```"):
        t = t.split("```")[1]
        if t.startswith("json"):
            t = t[4:]
    return json.loads(t.strip())


# ---- THE PROMPT (YOU WRITE THIS) -------------------------------------------
SYSTEM_PROMPT = """
you are an engineer agent. Your task is to solve the given problem by writing and running Python code. You have:
  1. The ONE tool: run_python(code) -> the code's stdout or its error traceback
  2. Output format: you MUST reply with ONLY a JSON object, one of:
       {"thought": "...", "action": "run_python", "action_input": "<python code>"}
       {"thought": "...", "final": "<answer>"}
  3. Rules: one action per turn; ALWAYS run code to verify before answering;
            use "final" only when the task is confirmed done.
"""


# ---- THE LOOP (YOU WRITE THIS) ---------------------------------------------
async def react(task: str, max_steps: int = 6) -> str:
    llm = LLM(system_prompt=SYSTEM_PROMPT)
    transcript = f"TASK: {task}"
    for step in range(1, max_steps + 1):
        # TODO 1: raw = await llm.aask(transcript)
        raw = await llm.aask(transcript, json_mode=True)
        # TODO 2: msg = parse(raw);  print(f"\n--- step {step} ---\n{msg}")
        msg = parse(raw)
        print(f"\n--- step {step} ---\n{msg}")
        # TODO 3: if "final" in msg -> return msg["final"]
        if "final" in msg:
            return msg["final"]
        # TODO 4: else look up TOOLS[msg["action"]], call it with msg["action_input"]
        #         -> observation
        else:
            action = msg["action"]
            action_input = msg["action_input"]
            if action not in TOOLS:
                return f"Error: unknown action '{action}'"
            observation = TOOLS[action](action_input)
        # TODO 5: append to transcript so the model sees what happened, e.g.:
        #         transcript += f"\n\nYOU: {raw}\n\nOBSERVATION: {observation}"
        transcript += f"\n\nYOU: {raw}\n\nOBSERVATION: {observation}"
    return "Stopped: hit max_steps without a final answer."


if __name__ == "__main__":
    task = ("Write a function fib(n) returning the nth Fibonacci number "
            "(fib(0)=0, fib(1)=1), then verify that fib(10) == 55 and report the result.")
    print("\n=== FINAL ===\n", asyncio.run(react(task)))
