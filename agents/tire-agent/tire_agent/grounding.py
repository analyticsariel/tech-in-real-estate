"""Runtime grounding validator (S20.D, decisions #139 and #149).

Checks a structured answer against the tool outputs from the same run:
- every number stated in the answer appears in a tool output (rounding allowed),
- every citation is a live site route,
- a `cannot_answer` reply quotes no metric numbers.
Returns a list of human-readable violations; empty means it passes.
"""

from __future__ import annotations

import json
import re

# Numbers that show up in plain prose without coming from data: window lengths, loan terms, ordinals.
# Exempt only when written as a bare integer ("3 months"). "5.0%", "5%", "$5" are measurements and get checked.
_PROSE_NUMBERS = {float(n) for n in [*range(13), 15, 30]}
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_MONTH_DATE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?(?:\s+\d{1,2},?)?\s+\d{4}\b",
    re.IGNORECASE,
)
_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
_NUMBER = re.compile(
    r"(?<![\w.])-?(\$)?(\d[\d,]*(?:\.\d+)?)\s*([kKmMbB](?![a-z]))?(\s*%)?"
)
_SCALE = {"k": 1e3, "m": 1e6, "b": 1e9}


def _scan(text: str) -> list[tuple[str, float, bool, str]]:
    """(literal, value, is_prose, raw) for each number in text, ignoring dates and bare years.

    `raw` is the number as written ("-$32.26", "5.0%"), so a UI can find it in the answer.
    """
    text = _MONTH_DATE.sub(" ", _ISO_DATE.sub(" ", text))
    text = _YEAR.sub(" ", text)
    out = []
    for m in _NUMBER.finditer(text):
        dollar, literal, scale, percent = m.groups()
        literal = literal.replace(",", "")
        value = float(literal) * _SCALE.get((scale or "").lower(), 1)
        bare_int = "." not in literal and not (dollar or scale or percent)
        out.append(
            (literal, value, bare_int and value in _PROSE_NUMBERS, m.group(0).strip())
        )
    return out


def numbers_in(text: str) -> list[tuple[str, float]]:
    """(literal, value) for every number in prose, ignoring dates and bare years."""
    return [(lit, v) for lit, v, _, _ in _scan(text)]


def checkable_numbers(text: str) -> list[tuple[str, float]]:
    """The numbers a grounded answer must back with tool data: everything except prose integers like "3 months"."""
    return [(lit, v) for lit, v, prose, _ in _scan(text) if not prose]


# Thousands separators count: skill and reading text says "800,000" where JSON would say 800000.
_TOOL_NUMBER = re.compile(
    r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
)


def _tool_values(tool_texts: list[str]) -> list[float]:
    # Dates are not values: "2026-11-05" would otherwise ground any 5, 11, or 2026 in the answer.
    return [
        abs(float(x.replace(",", "")))
        for t in tool_texts
        for x in _TOOL_NUMBER.findall(_ISO_DATE.sub(" ", t))
    ]


def _decimals(literal: str) -> int:
    return len(literal.split(".")[1]) if "." in literal else 0


def is_grounded(literal: str, value: float, tool_vals: list[float]) -> bool:
    """True if `value` is some tool value rounded to the answer's precision (sign-insensitive)."""
    d = _decimals(literal)
    v = abs(value)
    for t in tool_vals:
        if round(t, d) == round(v, d):
            return True
        # Scaled forms like "$422K" or "1.7M": compare at the stated precision.
        for scale in (1e3, 1e6, 1e9):
            if v >= scale and round(t / scale, max(d, 1)) == round(
                v / scale, max(d, 1)
            ):
                return True
    return False


def validate(answer, tool_texts: list[str], routes: set[str]) -> list[str]:
    """Violations for one structured answer (an object with status/answer/citations)."""
    violations = []
    nums = checkable_numbers(answer.answer)
    if answer.status == "cannot_answer":
        if nums:
            violations.append(
                f"declined but quoted numbers: {[lit for lit, _ in nums]}"
            )
    else:
        tool_vals = _tool_values(tool_texts)
        ungrounded = [lit for lit, v in nums if not is_grounded(lit, v, tool_vals)]
        if ungrounded:
            violations.append(f"numbers not found in tool results: {ungrounded}")
        if nums and not answer.citations:
            violations.append("states numbers but cites no page")
    bad = [c for c in answer.citations if c not in routes]
    if bad:
        violations.append(f"citations are not live site pages: {bad}")
    return violations


# Which date column dates a value column in metric_summary / observations rows.
_DATE_OF = {
    "latest_value": "latest_date",
    "aligned_value": "aligned_date",
    "value": "date",
}
_WINDOW = re.compile(r"(?:pct_)?change_(\d+m)|from_value_(\d+m)")


def _period(field: str, row: dict) -> str | None:
    if field in _DATE_OF:
        return row.get(_DATE_OF[field])
    m = _WINDOW.fullmatch(field)
    if not m:
        return None
    window = m.group(1) or m.group(2)
    start, end = row.get(f"from_date_{window}"), row.get("latest_date")
    if field.startswith("from_value") or not end:
        return start
    return f"{start} → {end}" if start else end


def _tool_rows(tool_texts: list[str]) -> list[dict]:
    """Structured rows from `query` ({columns, rows}) and `search` ({results}) outputs. Other text is skipped."""
    rows: list[dict] = []
    for text in tool_texts:
        try:
            data = json.loads(text)
        except ValueError:
            continue
        if not isinstance(data, dict):
            continue
        if isinstance(data.get("columns"), list) and isinstance(data.get("rows"), list):
            rows += [dict(zip(data["columns"], r, strict=False)) for r in data["rows"]]
        elif isinstance(data.get("results"), list):
            rows += [r for r in data["results"] if isinstance(r, dict)]
    return rows


def checked_figures(
    answer_text: str, tool_texts: list[str], citations: list[str]
) -> list[dict]:
    """Provenance for every checked number in a grounded answer, for the site's "where they came from" table.

    Each number is matched to the tool cell it came from (metric key, geography, column, period, url).
    Cells from cited pages win. `ambiguous` flags a number that matches more than one cell equally well;
    `source: "text"` means it matched prose (a skill or page text), not a data cell.
    """
    rows = _tool_rows(tool_texts)
    cited = set(citations)
    out = []
    for literal, value, prose, raw in _scan(answer_text):
        if prose:
            continue
        matches = [
            (row.get("url") in cited, field, row)
            for row in rows
            for field, cell in row.items()
            if isinstance(cell, int | float)
            and not isinstance(cell, bool)
            and is_grounded(literal, value, [abs(float(cell))])
        ]
        if not matches:
            out.append({"text": raw, "value": value, "source": "text"})
            continue
        best = [m for m in matches if m[0]] or matches
        _, field, row = best[0]
        # Same metric, place, and period under two columns (latest_value == aligned_value) is one fact.
        distinct = {
            (r.get("key"), r.get("geo_label") or r.get("geo_key"), _period(f, r))
            for _, f, r in best
        }
        ambiguous = len(distinct) > 1
        out.append(
            {
                "text": raw,
                "value": value,
                "source": "data",
                "field": field,
                "key": row.get("key"),
                "geo": row.get("geo_label") or row.get("geo_key"),
                "period": _period(field, row),
                "url": row.get("url"),
                "ambiguous": ambiguous,
                # Every period the number could be, so the site can say "Jan or Mar 2026" instead of guessing.
                **(
                    {"periods": sorted({p for *_, p in distinct} - {None})}
                    if ambiguous
                    else {}
                ),
            }
        )
    return out
