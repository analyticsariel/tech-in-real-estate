"""Turn golden.yaml into concrete examples against one tire.db build (decision #148).

- lint: every key / field / url a record references must exist, or this raises
- requires: SQL precondition; no rows -> the record is skipped and reported, never failed
- select: SQL rows fill {placeholders}; each row becomes one example (live trap cases)
- facts: resolved to their current value and frozen into the example
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import yaml

GOLDEN = Path(__file__).resolve().parent / "golden.yaml"
MAX_SKIP_RATIO = 0.10


class DatasetError(Exception):
    """Broken references or too many skipped records: the dataset, not the agent, needs fixing."""


def _fill(obj, row: dict):
    if isinstance(obj, str):
        return obj.format(**row)
    if isinstance(obj, list):
        return [_fill(x, row) for x in obj]
    if isinstance(obj, dict):
        return {k: _fill(v, row) for k, v in obj.items()}
    return obj


def _resolve_fact(db: sqlite3.Connection, fact: dict, columns: set[str]) -> dict:
    if fact["field"] not in columns:
        raise DatasetError(f"unknown metric_summary field {fact['field']!r}")
    sql = f"SELECT {fact['field']}, units, frequency FROM metric_summary WHERE key = ? AND role = ?"
    args = [fact["key"], fact["geo_role"]]
    if fact.get("geo_label"):
        sql += " AND geo_label = ?"
        args.append(fact["geo_label"])
    rows = db.execute(sql, args).fetchall()
    if len(rows) != 1:
        raise DatasetError(f"fact {fact} matched {len(rows)} rows; expected exactly 1")
    value, units, frequency = rows[0]
    return {**fact, "value": value, "units": units, "frequency": frequency}


def resolve(
    db_path: Path, git_sha: str, golden: Path = GOLDEN
) -> tuple[list[dict], list[str]]:
    """Return (examples, skipped_record_ids). Raises DatasetError on broken references or too many skips."""
    records = yaml.safe_load(golden.read_text())["records"]
    with closing(sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)) as db:
        routes = {r[0] for r in db.execute("SELECT url FROM routes")}
        columns = {r[1] for r in db.execute("PRAGMA table_info(metric_summary)")}
        examples, skipped, problems = [], [], []
        for rec in records:
            try:
                if rec.get("requires") and not db.execute(rec["requires"]).fetchall():
                    skipped.append(rec["id"])
                    continue
                if rec.get("select"):
                    cur = db.execute(rec["select"])
                    names = [d[0] for d in cur.description]
                    rows = [dict(zip(names, r, strict=True)) for r in cur.fetchall()]
                    if not rows:
                        skipped.append(rec["id"])
                        continue
                    concrete = [
                        {
                            **_fill(
                                {k: v for k, v in rec.items() if k != "select"}, row
                            ),
                            "id": f"{rec['id']}:{row['key']}",
                        }
                        for row in rows
                    ]
                else:
                    concrete = [rec]
                for c in concrete:
                    exp = c.get("expect", {})
                    for url in exp.get("cites", []) + exp.get("cites_any", []):
                        if url not in routes:
                            raise DatasetError(f"cites non-live route {url!r}")
                    facts = [
                        _resolve_fact(db, f, columns) for f in exp.get("facts", [])
                    ]
                    examples.append(
                        {
                            "id": c["id"],
                            "inputs": {"question": c["question"]},
                            "outputs": {
                                "category": c["category"],
                                "refuse": bool(exp.get("refuse")),
                                "cites": exp.get("cites", []),
                                "cites_any": exp.get("cites_any", []),
                                "must_not_cite": exp.get("must_not_cite", []),
                                "facts": facts,
                                "must_say": exp.get("must_say", []),
                                "must_not_say": exp.get("must_not_say", []),
                                "git_sha": git_sha,
                            },
                            "metadata": {
                                "record_id": rec["id"],
                                "category": c["category"],
                                "git_sha": git_sha,
                            },
                        }
                    )
            except (DatasetError, sqlite3.Error, KeyError) as exc:
                problems.append(f"{rec.get('id', '?')}: {exc}")
    if problems:
        raise DatasetError(
            "golden set has broken records:\n  - " + "\n  - ".join(problems)
        )
    if records and len(skipped) / len(records) > MAX_SKIP_RATIO:
        raise DatasetError(
            f"{len(skipped)}/{len(records)} records skipped (>{MAX_SKIP_RATIO:.0%}): {skipped}"
        )
    return examples, skipped
