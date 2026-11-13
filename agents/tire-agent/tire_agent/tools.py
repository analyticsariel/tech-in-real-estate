"""tire-agent tools: `search` (FTS5 over live pages) and `query` (read-only SQL). Decision #147.

Both read tire.db built by build_db.py. Neither raises to the model: every
failure comes back as {"error": ...} so the agent can recover or say it can't answer.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from langchain_core.tools import StructuredTool

DEFAULT_DB = Path(__file__).resolve().parent / "build" / "tire.db"
MAX_ROWS = 200
MAX_CHARS = 12_000
TIMEOUT_S = 0.5
SEARCH_LIMIT_MAX = 10
CANDIDATE_POOL = (
    120  # bm25 candidates re-ranked by coverage; readings share URLs with metric pages
)

# The authorizer allows reads only. Anything else (INSERT, ATTACH, PRAGMA, CREATE, ...) is denied.
_ALLOWED_ACTIONS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    sqlite3.SQLITE_RECURSIVE,
}
_DENIED_FUNCTIONS = {"load_extension", "readfile", "writefile", "edit", "fts5"}

_STOPWORDS = {
    "the",
    "and",
    "for",
    "what",
    "how",
    "which",
    "should",
    "does",
    "with",
    "about",
    "from",
    "that",
    "this",
    "are",
    "was",
    "has",
    "have",
    "can",
    "you",
    "your",
    "our",
    "tire",
    "metric",
    "metrics",
    "show",
    "tell",
    "look",
    "lately",
    "right",
    "now",
    "much",
    "many",
    "there",
    "any",
    "all",
}

COLUMN_NOTES = """\
metric_summary is pre-computed. Use it for every "latest / change / trend / compare" question:
  one row per metric (key) and geography. role = 'primary' (the page's featured geography) or 'benchmark'
  (Florida / United States comparison on the same page). latest_value at latest_date.
  {1m,3m,12m} windows: from_date_*, from_value_*, change_* (latest - from, in the metric's units;
  percent units -> percentage points), pct_change_* (relative %), direction_* ('rising'|'falling'|'flat').
  NULL means no observation for that window. Say it's not available; never substitute another month.
  streak_count / streak_direction: consecutive moves ending at the latest observation.
  aligned_value / aligned_date: a benchmark's value in the primary's latest month. Compare levels with this.
  aligned_{from_date,from_value,change,pct_change,direction}_{1m,3m,12m}: a benchmark's change over the
  primary's exact months. Compare changes with these, never with the benchmark's own change_*.
  is_forecast = 1: a projection (e.g. Zillow ZHVF/ZORF), not observed data. Read the forecasts table for it.
forecasts: horizon-shaped forecasts (Zillow ZHVF/ZORF). One row per horizon: value is the cumulative % change
  Zillow expects from base_month to target_month (horizon_months later). is_past = 1: that horizon has
  already ended, so it's an old forecast, not a prediction.
observations: raw history (key, geo_key, geo_label, role, date, value) for questions summary can't answer.
metrics: one row per metric page (title, units, frequency, geo_label, why_it_matters, url).
routes: every live site URL you may cite."""

EXAMPLES = """\
-- trend for one metric
SELECT latest_value, latest_date, change_3m, direction_3m, streak_count, streak_direction, url
FROM metric_summary WHERE key = 'mortgage_30y' AND role = 'primary';
-- county vs Florida vs US: levels in the same month, changes over the same months
SELECT geo_label, role, latest_value, latest_date, aligned_value, aligned_date,
       from_date_12m, change_12m, aligned_from_date_12m, aligned_change_12m, url
FROM metric_summary WHERE key = 'bls_hillsborough_unemployment_rate';
-- a published forecast, every horizon
SELECT geo_label, role, base_month, horizon_months, target_month, value, is_past, url
FROM forecasts WHERE key = 'zillow_zhvf' ORDER BY role DESC, horizon_months;
-- history question
SELECT date, value FROM observations
WHERE key = 'mortgage_30y' AND role = 'primary' AND date >= '2020-01-01' ORDER BY value DESC LIMIT 1;"""


def _authorizer(action, arg1, arg2, dbname, source):
    if action == sqlite3.SQLITE_FUNCTION and (arg2 or "").lower() in _DENIED_FUNCTIONS:
        return sqlite3.SQLITE_DENY
    # FTS5 reads `PRAGMA data_version` (a read-only change counter) on every MATCH. Allow only that, argument-free.
    if action == sqlite3.SQLITE_PRAGMA:
        return (
            sqlite3.SQLITE_OK
            if (arg1 or "").lower() == "data_version" and arg2 is None
            else sqlite3.SQLITE_DENY
        )
    return sqlite3.SQLITE_OK if action in _ALLOWED_ACTIONS else sqlite3.SQLITE_DENY


def connect(db_path: Path) -> sqlite3.Connection:
    """Read-only connection with the authorizer installed."""
    if not db_path.exists():
        raise FileNotFoundError(
            f"{db_path} not found. Run: python -m tire_agent.build_db"
        )
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.set_authorizer(_authorizer)
    return conn


def _run(
    conn: sqlite3.Connection, sql: str, params: tuple = (), capped: bool = True
) -> dict:
    """Execute under the timeout. `capped` applies the model-facing row/size caps; internal queries pass False."""
    deadline = time.monotonic() + TIMEOUT_S
    conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 10_000)
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchmany(MAX_ROWS + 1) if capped else cur.fetchall()
    except sqlite3.DatabaseError as exc:
        msg = str(exc)
        if "interrupted" in msg:
            msg = f"query exceeded {TIMEOUT_S}s; narrow it (filter by key, add LIMIT)"
        elif "not authorized" in msg or "prohibited" in msg:
            msg = "read-only: only SELECT queries over tire.db are allowed"
        return {"error": msg}
    finally:
        conn.set_progress_handler(None, 0)
    columns = [d[0] for d in cur.description or []]
    if not capped:
        return {"columns": columns, "rows": [list(r) for r in rows], "truncated": False}
    truncated = len(rows) > MAX_ROWS
    out = {
        "columns": columns,
        "rows": [list(r) for r in rows[:MAX_ROWS]],
        "truncated": truncated,
    }
    text = json.dumps(out, default=str)
    while len(text) > MAX_CHARS and out["rows"]:
        out["rows"] = (
            out["rows"][: max(1, len(out["rows"]) // 2)] if len(out["rows"]) > 1 else []
        )
        out["truncated"] = True
        text = json.dumps(out, default=str)
    if out["truncated"]:
        out["note"] = "results truncated; add filters or LIMIT"
    return out


def schema_text(conn: sqlite3.Connection) -> str:
    tables = ["metric_summary", "forecasts", "observations", "metrics", "routes"]
    lines = []
    for t in tables:
        cols = [r[0] for r in conn.execute(f"SELECT * FROM {t} LIMIT 0").description]
        lines.append(f"{t}({', '.join(cols)})")
    return "\n".join(lines)


# bm25 column weights: a word in the title, key, or tags (label, geography, category) counts far more than the
# same word repeated in a long reading body. Results are then re-ranked by how many query words they cover.
_BM25 = (
    "bm25(pages, 0.0, 6.0, 10.0, 0.0, 5.0, 1.0)"  # kind, key, title, url, tags, body
)


def _terms(text: str) -> list[str]:
    words = [
        w
        for w in re.findall(r"[a-z0-9]+", text.lower())
        if (len(w) > 2 or w.isdigit()) and w not in _STOPWORDS
    ]
    return list(dict.fromkeys(words))


def _has_word(term: str, text: str) -> bool:
    stem = term[:-1] if term.endswith("s") and len(term) > 3 else term
    return re.search(rf"\b{re.escape(stem)}(s|es)?\b", text) is not None


def _coverage(terms: list[str], text: str, geo: str | None) -> float:
    """Query words found in a page's key/title/tags, plus half a point per word matching the page's
    geography: a tiebreaker so "Tampa rent" prefers Tampa rent pages without outranking the topic."""
    text = text.lower().replace("_", " ").replace("-", " ")
    geo = (geo or "").lower().replace("-", " ")
    text_hits = {t for t in terms if _has_word(t, text)}
    geo_hits = {t for t in terms if _has_word(t, geo)}
    # The place bonus only counts when the page also matches the topic, so "Hillsborough unemployment"
    # doesn't surface every Hillsborough page.
    return len(text_hits) + (0.5 * len(geo_hits) if text_hits - geo_hits else 0.0)


def search_pages(conn: sqlite3.Connection, query: str, limit: int = 6) -> dict:
    """FTS5 search over live pages, enriched with each metric's latest value and units."""
    terms = _terms(query)
    if not terms:
        return {"error": "no searchable words; describe the metric, place, or skill"}
    fts = " OR ".join(f'"{t}"' for t in terms)
    limit = max(1, min(int(limit), SEARCH_LIMIT_MAX))
    res = _run(
        conn,
        """
        SELECT p.kind, p.key, p.title, p.url, p.tags, snippet(pages, 5, '', '', ' … ', 14) AS snippet,
               m.units, m.geo_label, m.why_it_matters,
               s.latest_value, s.latest_date, s.is_forecast
        FROM pages p
        LEFT JOIN metrics m ON m.key = p.key AND p.kind IN ('metric', 'reading')
        LEFT JOIN metric_summary s ON s.key = p.key AND s.role = 'primary' AND p.kind IN ('metric', 'reading')
        WHERE pages MATCH ? ORDER BY {_BM25} LIMIT ?""".replace("{_BM25}", _BM25),
        (fts, CANDIDATE_POOL),
        capped=False,
    )
    if "error" in res:
        return res
    rows = [dict(zip(res["columns"], r, strict=True)) for r in res["rows"]]
    # Stable sort: most query words covered in key/title/tags first, bm25 order within ties.
    rows.sort(
        key=lambda r: (
            -_coverage(terms, f"{r['key']} {r['title']} {r['tags']}", r["geo_label"])
        )
    )
    hits, seen = [], set()
    for row in rows:
        row.pop("tags")
        if row["url"] in seen:
            continue  # a metric page and its reading share a URL; keep the first (best-ranked)
        seen.add(row["url"])
        hit = {k: v for k, v in row.items() if v is not None}
        if hit.get("kind") == "reading":
            hit["kind"] = "metric"
        if "why_it_matters" in hit:
            hit["why_it_matters"] = hit["why_it_matters"][:240]
        hits.append(hit)
        if len(hits) == limit:
            break
    # Words that appear nowhere on the site (e.g. "austin") tell the agent the site can't answer that part.
    unmatched = [
        t
        for t in terms
        if not _run(
            conn, "SELECT 1 FROM pages WHERE pages MATCH ? LIMIT 1", (f'"{t}"',)
        ).get("rows")
    ]
    if not hits:
        return {
            "error": "no matching pages",
            "unmatched_terms": unmatched,
            "hint": "the site covers Tampa / Hillsborough County, Florida, and US data",
        }
    return (
        {"results": hits, "unmatched_terms": unmatched}
        if unmatched
        else {"results": hits}
    )


def make_tools(db_path: Path | None = None) -> list[StructuredTool]:
    """Build the two tools. The schema in `query`'s description is read from the DB.

    Each call opens its own read-only connection. The agent runs parallel tool calls on separate threads,
    and a shared connection deadlocked (SQLite's mutex held while the progress handler waited for the GIL,
    and vice versa). Opening a connection to the ~3 MB file costs about a millisecond.
    """
    db_path = Path(db_path or os.environ.get("TIRE_DB", DEFAULT_DB))
    with closing(connect(db_path)) as conn:  # also fails fast if the DB is missing
        tables = schema_text(conn)

    def search(query: str, limit: int = 6) -> dict:
        with closing(connect(db_path)) as conn:
            return search_pages(conn, query, limit)

    def query(sql: str) -> dict:
        with closing(connect(db_path)) as conn:
            return _run(conn, sql)

    search_tool = StructuredTool.from_function(
        search,
        name="search",
        description=(
            "Find TiRE site pages (metrics, skills, site pages) for a plain-English question. "
            "Metric hits include key, url, geography, units, latest value/date, why it matters, and is_forecast, "
            "enough to recommend pages without querying each. Use the key with `query` for exact numbers. "
            "`unmatched_terms` lists words that appear nowhere on the site: if a place or topic is unmatched, "
            "the site has no data on it, so say so instead of answering with something else."
        ),
    )
    query_tool = StructuredTool.from_function(
        query,
        name="query",
        description=(
            "Run ONE read-only SQLite SELECT against tire.db and get back columns + rows (max "
            f"{MAX_ROWS} rows). Quote numbers exactly as returned; never compute your own. Cite the `url` column.\n\n"
            f"Tables:\n{tables}\n\n{COLUMN_NOTES}\n\nExamples:\n{EXAMPLES}"
        ),
    )
    return [search_tool, query_tool]
