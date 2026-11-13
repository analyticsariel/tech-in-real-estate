"""CLI: python -m tire_agent ask "question" [--model claude-sonnet-5-5]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    ap = argparse.ArgumentParser(prog="python -m tire_agent")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ask", help="ask tire-agent one question")
    p.add_argument("question")
    p.add_argument("--model")
    args = ap.parse_args()

    from tire_agent.agent import build_agent
    from tire_agent.ask import ask, record_feedback

    agent = build_agent(model=args.model)
    r = ask(agent, args.question)
    record_feedback(r)
    print(f"\n[{r.status}] {r.answer}\n")
    for c in r.citations:
        print(f"  -> {c}")
    print(
        f"\nmodel: {agent.model}  model calls: {r.model_calls}  tool calls: {r.tool_calls}  "
        f"cost: ${r.cost_usd:.4f}  latency: {r.latency_s}s  retried: {r.retried}"
    )
    if r.fallback_reason:
        print(f"fallback: {r.fallback_reason}" + (f"  ({r.error})" if r.error else ""))
    if r.violations:
        print(f"violations: {r.violations}")
    print(f"LangSmith run ids: {', '.join(r.run_ids)}")
    return 1 if r.error else 0


if __name__ == "__main__":
    sys.exit(main())
