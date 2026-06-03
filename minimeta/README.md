# minimeta — MetaGPT's capabilities, built on modern frameworks

A learning project: reproduce MetaGPT's headline capability — a *team of agents
that turns one requirement into a software design and code* — but built on
**LangGraph** (the modern orchestration standard), with **MCP** for tools.

The teaching twist: at each phase we also look at the **"what if this framework
didn't exist?"** version — the plumbing we'd hand-roll — so the framework earns
its place instead of being magic.

## Mental model

    LangGraph StateGraph        ← the orchestrator (replaces Team + Environment)
      ├ State (TypedDict)       ← shared memory passed between steps (replaces Memory + Message bus)
      ├ Nodes (functions)       ← one agent step = one LLM call (our llm.py lives here)
      └ Edges (incl. conditional) ← who runs next (replaces _watch / pub-sub routing)

Map to what we almost built by hand:
| Hand-rolled (old plan) | LangGraph gives us           |
|------------------------|------------------------------|
| Message schema, Memory | the **State** object         |
| Environment routing    | **edges** (esp. conditional) |
| Role observe→think→act | a **node** function          |
| Team.run() loop        | `graph.invoke()` / `.stream()` |

## Roadmap

### Part 1 — Foundations (workflows)  ✅ DONE
- [x] Phase 0  — Scaffold (folder, package, venv)
- [x] Phase 1  — LLM wrapper: async `aask()` around Gemini        (llm.py)
- [x] Phase 2  — LangGraph fundamentals: State, nodes, edges, reducers (hello_graph.py)
- [x] Phase 3  — WARM-UP: 2-agent debate as a cyclic graph (conditional edges + loop)
- [x] Phase 4  — The SOP: ProductManager → Architect → Engineer (workflow, fixed path)

### Part 2 — Real agents (the workflow → agent leap)
- [x] Phase 5  — Prompt anatomy + HAND-ROLL a ReAct loop: 1 agent, a tool, think→act→observe
- [x] Phase 6  — Swap to LangGraph `create_react_agent`; give the Engineer real tools (write_file, run_python) → self-correcting code agent
- [x] Phase 7  — Reflexion: agent critiques and revises its own output

### Part 3 — The agentic software company (MetaGPT, for real)
- [x] Phase 8  — Supervisor pattern: a boss agent DELEGATES to PM/Architect/Engineer and decides who runs next (agent-driven control flow)
- [x] Phase 9  — Assemble it: supervisor + specialist agents + tools → writes a real project to disk, with a QA agent that runs the code (PM→Architect→Engineer→QA→FINISH, verified PASS)
- [ ] Phase 10 — Polish (logging, retries, cost, streaming) + compare to the real MetaGPT; where MCP / A2A fit

> **Prompt-craft is a graded skill here.** From Phase 5 on, *you* draft every
> system prompt and tool description; I review them like a senior would. Tool
> docstrings are prompts too — the agent reads them to decide what to call.

## Run things with the project venv

    ..\.venv\Scripts\python.exe -m minimeta.examples.debate
