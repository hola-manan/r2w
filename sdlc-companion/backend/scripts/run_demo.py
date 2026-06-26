"""Run the scripted walkthrough against a LIVE backend (requires a real API key).

Usage (with the server running on :8000 and GOOGLE_API_KEY set):
    python -m scripts.run_demo --profile eu-fintech
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx

WALKTHROUGH = Path(__file__).resolve().parents[1] / "data" / "demo" / "walkthrough.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--profile", default="eu-fintech")
    ap.add_argument("--name", default="Demo walkthrough")
    args = ap.parse_args()

    wt = json.loads(WALKTHROUGH.read_text(encoding="utf-8"))
    c = httpx.Client(base_url=args.base, timeout=120)

    pid = c.post("/projects", json={"name": args.name, "profile_id": args.profile}).json()["id"]
    print(f"project {pid} ({args.profile})")

    for stage in wt["stages"]:
        for msg in stage["messages"]:
            print(f"\n[stage {stage['stage']} / {stage['persona']}] > {msg}")
            turn = c.post(f"/projects/{pid}/message",
                          json={"message": msg, "persona": stage["persona"]}).json()
            print("  reply:", turn["reply"][:300])
            card = turn["scorecard"]
            print(f"  gate_passed={card['gate_passed']} blockers={card['blockers']}")
            if turn.get("escalation"):
                print("  escalation:", turn["escalation"])
        adv = c.post(f"/projects/{pid}/advance").json()
        print(f"  advance -> advanced={adv['advanced']} stage={adv['new_stage']}")

    graph = c.get(f"/projects/{pid}/graph").json()
    print(f"\nFinal graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")


if __name__ == "__main__":
    main()
