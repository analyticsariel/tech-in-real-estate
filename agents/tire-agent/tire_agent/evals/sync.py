"""Mirror the resolved golden set into the LangSmith dataset `tire-agent-golden` (decision #148).

    python -m tire_agent.evals.sync

Exact mirror: example IDs are derived from record IDs, stale examples are deleted, and the
resulting dataset version is tagged with the tire.db build's git sha.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
import sys
import uuid
from contextlib import closing
from pathlib import Path

from dotenv import load_dotenv

from tire_agent.agent import DEFAULT_BUILD
from tire_agent.evals.resolve import DatasetError, resolve

DATASET = "tire-agent-golden"


def example_uuid(example_id: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"tire-agent-golden/{example_id}")


def build_sha(db_path: Path) -> str:
    with closing(sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)) as db:
        return db.execute(
            "SELECT value FROM build_info WHERE name = 'git_sha'"
        ).fetchone()[0]


def sync(db_path: Path = DEFAULT_BUILD / "tire.db") -> dict:
    from langsmith import Client

    sha = build_sha(db_path)
    examples, skipped = resolve(db_path, sha)
    client = Client()
    if not client.has_dataset(dataset_name=DATASET):
        client.create_dataset(
            DATASET,
            description="tire-agent golden set (tire_agent/evals/golden.yaml)",
        )
    dataset = client.read_dataset(dataset_name=DATASET)
    existing = {str(e.id) for e in client.list_examples(dataset_id=dataset.id)}
    wanted = {str(example_uuid(e["id"])): e for e in examples}
    payload = lambda e: {
        "id": example_uuid(e["id"]),
        "inputs": e["inputs"],
        "outputs": e["outputs"],
        "metadata": e["metadata"],
    }
    if stale := sorted(existing - set(wanted)):
        client.delete_examples(example_ids=stale)
    if new := [payload(e) for i, e in wanted.items() if i not in existing]:
        client.create_examples(dataset_id=dataset.id, examples=new)
    if updates := [payload(e) for i, e in wanted.items() if i in existing]:
        client.update_examples(dataset_id=dataset.id, updates=updates)
    tag = f"sha-{sha[:12]}"
    client.update_dataset_tag(
        dataset_id=dataset.id, as_of=dt.datetime.now(dt.UTC), tag=tag
    )
    return {
        "dataset": DATASET,
        "examples": len(examples),
        "skipped": skipped,
        "deleted": len(stale),
        "created": len(new),
        "updated": len(updates),
        "tag": tag,
    }


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[3] / ".env")
    try:
        print(sync())
    except DatasetError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
