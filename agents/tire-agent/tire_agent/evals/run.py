"""Run a LangSmith experiment on `tire-agent-golden` and check the eval gate (decisions #149, #161).

    python -m tire_agent.evals.run --model claude-haiku-5-5

Gate: correct_answer >= 95%, citations, budget and plain_dates 100%. Exits 1 if the gate fails.
Examples that fail any gate metric are re-run once, as a second experiment. A passing retry replaces the
miss; a failing retry stands. With 11 examples, one stochastic miss would otherwise drop correct_answer
to 91% and block a deploy.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

from tire_agent.evals.evaluators import (
    budget,
    correct_answer,
    make_citations,
    plain_dates,
)
from tire_agent.evals.sync import DATASET, build_sha

GATE = {"correct_answer": 0.95, "citations": 1.0, "budget": 1.0, "plain_dates": 1.0}


def failed_ids(rows: list[dict]) -> list[str]:
    """Examples that missed any gate metric."""
    return [r["example_id"] for r in rows if not all(r.get(k) for k in GATE)]


def merge_retries(first: list[dict], retries: list[dict]) -> list[dict]:
    """First-run rows, with each retried example replaced by its retry (marked `retried`)."""
    again = {r["example_id"]: {**r, "retried": True} for r in retries}
    return [again.get(r["example_id"], r) for r in first]


def gate_rates(rows: list[dict]) -> dict[str, float]:
    return {k: sum(r.get(k, 0) for r in rows) / len(rows) for k in GATE}


async def run(
    model: str, examples=None, prefix: str = "", concurrency: int = 4
) -> tuple[list[dict], str]:
    """One experiment over the dataset, or over `examples` (a retry). Returns rows and the experiment name."""
    from langsmith import Client

    from tire_agent.agent import build_agent
    from tire_agent.ask import aask

    agent = build_agent(model=model)

    async def target(inputs: dict) -> dict:
        r = await aask(agent, inputs["question"])
        return {
            "status": r.status,
            "answer": r.answer,
            "citations": r.citations,
            "tool_calls": r.tool_calls,
            "model_calls": r.model_calls,
            "cost_usd": r.cost_usd,
            "latency_s": r.latency_s,
            "fallback_reason": r.fallback_reason,
            "retried": r.retried,
        }

    results = await Client().aevaluate(
        target,
        data=examples if examples is not None else DATASET,
        evaluators=[correct_answer, make_citations(agent.routes), budget, plain_dates],
        experiment_prefix=f"tire-agent-{model}{prefix}",
        metadata={"model": model, "git_sha": build_sha(agent.db_path)},
        max_concurrency=concurrency,
    )
    rows = []
    async for row in results:
        scores = {r.key: r.score for r in row["evaluation_results"]["results"]}
        comments = {
            r.key: r.comment
            for r in row["evaluation_results"]["results"]
            if r.comment and not r.score
        }
        out = row["run"].outputs or {}
        rows.append(
            {
                "example_id": str(row["example"].id),
                "question": row["example"].inputs["question"],
                **scores,
                "comments": comments,
                "cost_usd": out.get("cost_usd", 0.0),
                "latency_s": out.get("latency_s", 0.0),
            }
        )
    return rows, results.experiment_name


async def run_with_retry(model: str) -> tuple[list[dict], list[str]]:
    from langsmith import Client

    rows, name = await run(model)
    names = [name]
    missed = failed_ids(rows)
    if missed:
        examples = list(
            Client().list_examples(dataset_name=DATASET, example_ids=missed)
        )
        retry_rows, retry_name = await run(model, examples=examples, prefix="-retry")
        rows = merge_retries(rows, retry_rows)
        names.append(retry_name)
    return rows, names


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[3] / ".env")
    ap = argparse.ArgumentParser(prog="python -m tire_agent.evals.run")
    ap.add_argument("--model", default="claude-haiku-5-5")
    args = ap.parse_args()
    rows, names = asyncio.run(run_with_retry(args.model))
    for r in rows:
        flags = " ".join(f"{k}:{'PASS' if r.get(k) else 'fail'}" for k in GATE)
        tag = " (retry)" if r.get("retried") else ""
        print(
            f"{flags}  ${r['cost_usd']:.4f} {r['latency_s']:>5}s  {r['question'][:60]}{tag}"
        )
        for k, c in r["comments"].items():
            print(f"      {k}: {c}")
    n = len(rows)
    print(
        f"\nexperiment: {' + '.join(names)}  examples: {n}  retried: {sum(1 for r in rows if r.get('retried'))}"
    )
    print(
        f"mean cost ${sum(r['cost_usd'] for r in rows) / n:.4f}  mean latency {sum(r['latency_s'] for r in rows) / n:.1f}s"
    )
    rates = gate_rates(rows)
    passed = all(rates[k] >= t for k, t in GATE.items())
    for k, t in GATE.items():
        print(f"{k:15s} {rates[k]:.0%} (gate {t:.0%})")
    print("GATE: PASS" if passed else "GATE: FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
