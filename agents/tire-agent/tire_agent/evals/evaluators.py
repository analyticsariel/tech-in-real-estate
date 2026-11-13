"""The code evaluators (decisions #149, #168): correct_answer, citations, budget, plain_dates.

Each takes the target's outputs and the example's frozen reference outputs and returns
{"key", "score", "comment"}. Matching is unit-aware and tolerant of phrasing:
direction synonyms ("rose" = rising), dates in ISO or "Month YYYY" form, rounding to the
answer's own precision, and NULL truth satisfied only by saying the value isn't available.
"""

from __future__ import annotations

import datetime as dt
import re

from tire_agent.agent import MAX_TOOL_CALLS
from tire_agent.grounding import checkable_numbers, numbers_in

DIRECTION_WORDS = {
    "rising": r"rising|rose|risen|up|increas\w*|higher|gain\w*|climb\w*",
    "falling": r"falling|fell|fallen|down|declin\w*|lower|drop\w*|decreas\w*",
    "flat": r"flat|unchanged|steady|little changed|essentially flat|about the same",
}
NOT_AVAILABLE = r"not available|isn't available|unavailable|no data|not published|no reading|no observation"
NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}


def _has(pattern: str, text: str) -> bool:
    return re.search(rf"\b(?:{pattern})\b", text, re.IGNORECASE) is not None


def _date_ok(iso: str, frequency: str | None, text: str) -> bool:
    d = dt.date.fromisoformat(iso)
    t = text.replace(",", "")
    forms = [iso, d.strftime("%B %-d %Y"), d.strftime("%b %-d %Y")]
    if frequency in (None, "monthly", "quarterly", "annual"):
        forms += [d.strftime("%B %Y"), d.strftime("%b %Y"), iso[:7]]
    return any(f.lower() in t.lower() for f in forms)


def _number_ok(truth: float, units: str | None, text: str) -> bool:
    for literal, value in numbers_in(text):
        decimals = len(literal.split(".")[1]) if "." in literal else 0
        rounding = 0.5 * 10**-decimals
        tol = (
            max(0.01, rounding)
            if units == "percent"
            else max(abs(truth) * 0.005, rounding)
        )
        if abs(abs(value) - abs(truth)) <= tol:
            return True
    return False


def fact_ok(fact: dict, text: str) -> bool:
    value, field = fact["value"], fact["field"]
    if value is None:
        return _has(NOT_AVAILABLE, text)
    if field.startswith("direction_") or field == "streak_direction":
        return _has(DIRECTION_WORDS[value], text)
    if field.endswith("_date") or field.startswith("from_date"):
        return _date_ok(value, fact.get("frequency"), text)
    if field == "streak_count":
        word = next((w for w, n in NUMBER_WORDS.items() if n == value), None)
        return _has(str(value) + (f"|{word}" if word else ""), text)
    return _number_ok(float(value), fact.get("units"), text)


def correct_answer(outputs: dict, reference_outputs: dict) -> dict:
    text, status = outputs.get("answer", ""), outputs.get("status")
    if reference_outputs["refuse"]:
        nums = [lit for lit, _ in checkable_numbers(text)]
        ok = status == "cannot_answer" and not nums
        return {
            "key": "correct_answer",
            "score": int(ok),
            "comment": None
            if ok
            else f"should decline with no numbers (status={status}, numbers={nums})",
        }
    missing = [
        f"{f['field']}={f['value']}"
        for f in reference_outputs["facts"]
        if not fact_ok(f, text)
    ]
    ok = status == "answered" and not missing
    return {
        "key": "correct_answer",
        "score": int(ok),
        "comment": None if ok else f"status={status}; missing {missing}",
    }


def make_citations(routes: set[str]):
    def citations(outputs: dict, reference_outputs: dict) -> dict:
        cites = set(outputs.get("citations", []))
        problems = []
        if missing := set(reference_outputs["cites"]) - cites:
            problems.append(f"missing {sorted(missing)}")
        if reference_outputs["cites_any"] and not cites & set(
            reference_outputs["cites_any"]
        ):
            problems.append("none of cites_any")
        if bad := [
            c
            for c in cites
            for p in reference_outputs["must_not_cite"]
            if c.startswith(p)
        ]:
            problems.append(f"forbidden {bad}")
        if dead := sorted(cites - routes):
            problems.append(f"not live {dead}")
        return {
            "key": "citations",
            "score": int(not problems),
            "comment": "; ".join(problems) or None,
        }

    return citations


ISO_DATE = re.compile(r"\b\d{4}-\d{2}(?:-\d{2})?\b")


def plain_dates(outputs: dict) -> dict:
    """Dates in prose are written in words ("January 2026"), never ISO (decision #168)."""
    found = ISO_DATE.findall(outputs.get("answer", ""))
    return {
        "key": "plain_dates",
        "score": int(not found),
        "comment": f"ISO dates in prose: {found}" if found else None,
    }


def budget(outputs: dict) -> dict:
    n = outputs.get("tool_calls", 0)
    return {
        "key": "budget",
        "score": int(n <= MAX_TOOL_CALLS),
        "comment": f"{n} attempted tool calls",
    }
