"""Drive the staged blocked->pass walkthrough against a LIVE backend (needs a real API key).

For each step it sends the message, prints the agent reply + readiness scorecard (the LLM's
per-dimension scoring) + any escalation, then attempts POST /advance and checks the result
against the step's `expect_advanced`. So the run visibly shows Advance BLOCKED after the
first message of each stage and PASSED after the second.

Usage (server on :8000, GOOGLE_API_KEY set):
    python -m scripts.run_demo --profile eu-fintech [--verbose]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

WALKTHROUGH = Path(__file__).resolve().parents[1] / "data" / "demo" / "walkthrough.json"
_RAG = {"green": "●", "amber": "◐", "red": "○"}


def _print_scorecard(card: dict, verbose: bool) -> None:
    print(
        f"    gate_passed={card['gate_passed']}  "
        f"weighted_soft={card['weighted_soft']}/{card['threshold']}"
    )
    if card["blockers"]:
        print(f"    blockers (hard dims not green): {card['blockers']}")
    if verbose:
        for d in card["dimensions"]:
            mark = _RAG.get(d["rag"], "?")
            print(f"      {mark} [{d['kind']}] {d['name']}: L{d['level']} — {d['justification'][:110]}")
            if d.get("followup_question"):
                print(f"          ask: {d['followup_question'][:110]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--profile", default="eu-fintech")
    ap.add_argument("--name", default="Demo walkthrough")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    wt = json.loads(WALKTHROUGH.read_text(encoding="utf-8"))
    c = httpx.Client(base_url=args.base, timeout=240)

    pid = c.post("/projects", json={"name": args.name, "profile_id": args.profile}).json()["id"]
    print(f"project {pid} ({args.profile}): {wt.get('title', '')}\n")

    failures: list[str] = []
    for stage in wt["stages"]:
        snum, persona = stage["stage"], stage["persona"]
        print(f"=== Stage {snum} ({persona}) ===")
        for i, step in enumerate(stage["steps"], 1):
            msg, expect = step["message"], step["expect_advanced"]
            want = "PASS" if expect else "BLOCK"
            preview = msg if len(msg) <= 150 else msg[:150] + "…"
            print(f"\n[S{snum} step {i} · expect {want}] > {preview}")

            resp = c.post(f"/projects/{pid}/message", json={"message": msg, "persona": persona})
            if resp.status_code != 200:
                print(f"  ! message error {resp.status_code}: {resp.text[:200]}")
                failures.append(f"S{snum}.{i} message HTTP {resp.status_code}")
                break
            turn = resp.json()
            if turn.get("reply"):
                print("  reply:", turn["reply"][:240].replace("\n", " "))
            if turn.get("escalation"):
                print("  escalation:", json.dumps(turn["escalation"])[:220])
            if turn.get("scorecard"):
                _print_scorecard(turn["scorecard"], args.verbose)

            adv = c.post(f"/projects/{pid}/advance").json()
            got = bool(adv.get("advanced"))
            ok = got == expect
            flag = "OK" if ok else "MISMATCH"
            print(f"  -> advance: advanced={got} (expected {expect})  [{flag}]")
            if adv.get("blocked_by_stale"):
                print(f"     blocked_by_stale: {adv['blocked_by_stale']}")
            if not ok:
                failures.append(f"S{snum}.{i} expected advanced={expect}, got {got}")

    proj = c.get(f"/projects/{pid}").json()
    graph = c.get(f"/projects/{pid}/graph").json()
    counts: dict[str, int] = {}
    for n in graph["nodes"]:
        counts[n["doc_type"]] = counts.get(n["doc_type"], 0) + 1
    chosen = [n.get("chosen") for n in graph["nodes"] if n["doc_type"] == "adr" and n.get("chosen")]
    print(f"\nFinal stage {proj['current_stage']}  gate_status={proj['gate_status']}")
    print(f"Graph: {len(graph['nodes'])} nodes {counts}, {len(graph['edges'])} edges")
    print(f"Chosen technologies (ADRs): {chosen}")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("\nAll stages blocked-then-passed as expected.")


if __name__ == "__main__":
    main()
