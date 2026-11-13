"""Pre-computed facts per series: windows, direction, streaks (decision #147).

All arithmetic tire-agent answers with lives here, not in the model. Pure
functions over a list of {"date": "YYYY-MM-DD", "value": float} observations
sorted by date.

Window rule (calendar-month matching, frequency-aware):
- monthly / quarterly / annual: the observation in the target calendar month.
- daily / weekly: the last observation on or before the same day of the
  target month (day clamped to month end), at most MAX_GAP_DAYS earlier.
- No match means None. Never fall back to a neighbouring month.
"""

from __future__ import annotations

import calendar
import datetime as dt
import itertools

LOW_FREQ = {"monthly", "quarterly", "annual"}
SUB_MONTHLY = {"daily", "weekly"}
FREQUENCIES = LOW_FREQ | SUB_MONTHLY
WINDOWS = {"1m": 1, "3m": 3, "12m": 12}
WINDOW_FIELDS = ("from_date", "from_value", "change", "pct_change", "direction")
MAX_GAP_DAYS = 14

# Direction bands, approved 2026-11-06 (decision #153).
FLAT_PP_FOR_PERCENT = 0.05
FLAT_RELATIVE = 0.005


def _d(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def shift_months(d: dt.date, months: int) -> dt.date:
    """Same day `months` earlier (negative) or later, clamped to month end."""
    idx = d.year * 12 + d.month - 1 + months
    y, m = divmod(idx, 12)
    m += 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def period_start(d: dt.date, frequency: str) -> dt.date:
    """First day of the period an observation dated `d` stands for.

    Sources label periods differently (HUD dates fiscal-year rents at period
    end), so "is this a forecast?" compares the period's start, not its label.
    """
    if frequency == "daily":
        return d
    if frequency == "weekly":
        return d - dt.timedelta(days=6)
    if frequency == "monthly":
        return d.replace(day=1)
    if frequency == "quarterly":
        return dt.date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)
    if frequency == "annual":
        return dt.date(d.year, 1, 1)
    raise ValueError(f"unknown frequency {frequency!r}")


def is_forecast(latest_date: str, frequency: str, today: dt.date) -> bool:
    """True when the latest value's period hasn't started yet (e.g. Zillow ZHVF/ZORF)."""
    return period_start(_d(latest_date), frequency) > today


def value_at(obs: list[dict], frequency: str, target: dt.date) -> dict | None:
    """The observation that represents `target` under the window rule."""
    if frequency not in FREQUENCIES:
        raise ValueError(f"unknown frequency {frequency!r}")
    if frequency in LOW_FREQ:
        hits = [
            o
            for o in obs
            if (_d(o["date"]).year, _d(o["date"]).month) == (target.year, target.month)
        ]
        return hits[-1] if hits else None
    earlier = [o for o in obs if _d(o["date"]) <= target]
    if not earlier or (target - _d(earlier[-1]["date"])).days > MAX_GAP_DAYS:
        return None
    return earlier[-1]


def direction(change: float, base: float, units: str | None) -> str:
    if units == "percent":
        flat = abs(change) < FLAT_PP_FOR_PERCENT
    else:
        flat = base == 0 or abs(change) / abs(base) < FLAT_RELATIVE
    if flat:
        return "flat"
    return "rising" if change > 0 else "falling"


def window(
    obs: list[dict], frequency: str, months: int, units: str | None
) -> dict | None:
    latest = obs[-1]
    base = value_at(obs, frequency, shift_months(_d(latest["date"]), -months))
    if base is None or base is latest:
        return None
    change = round(latest["value"] - base["value"], 6)
    return {
        "from_date": base["date"],
        "from_value": base["value"],
        "change": change,
        "pct_change": round(100 * change / base["value"], 4) if base["value"] else None,
        "direction": direction(change, base["value"], units),
    }


def streak(obs: list[dict]) -> dict:
    """Consecutive same-direction moves ending at the latest observation."""
    diffs = [b["value"] - a["value"] for a, b in itertools.pairwise(obs)]
    if not diffs or diffs[-1] == 0:
        return {"count": 0, "direction": "flat"}
    up = diffs[-1] > 0
    n = 0
    for d in reversed(diffs):
        if d != 0 and (d > 0) == up:
            n += 1
        else:
            break
    return {"count": n, "direction": "rising" if up else "falling"}


def summarize(obs: list[dict], frequency: str, units: str | None) -> dict:
    """Flat dict of summary columns for one series."""
    if not obs:
        raise ValueError("no observations")
    latest = obs[-1]
    row = {"latest_date": latest["date"], "latest_value": latest["value"]}
    for name, months in WINDOWS.items():
        w = window(obs, frequency, months, units) or {}
        for field in WINDOW_FIELDS:
            row[f"{field}_{name}"] = w.get(field)
    s = streak(obs)
    row["streak_count"], row["streak_direction"] = s["count"], s["direction"]
    return row


def aligned_windows(
    obs: list[dict], frequency: str, units: str | None, through: str
) -> dict:
    """A benchmark's windows ending at `through` (the primary's latest month), so a county's change is
    compared with Florida's and the US's change over the same months, not each series' own latest."""
    upto = [o for o in obs if o["date"] <= through]
    row = {}
    for name, months in WINDOWS.items():
        w = window(upto, frequency, months, units) if upto else None
        for field in WINDOW_FIELDS:
            row[f"aligned_{field}_{name}"] = (w or {}).get(field)
    return row


def forecast_horizons(
    obs: list[dict], horizons: list[int], today: dt.date
) -> list[dict]:
    """Rows for a horizon-shaped forecast (Zillow ZHVF/ZORF): one cumulative % change per horizon from a
    shared base month, each dated at its horizon's end. Raises if the data doesn't have that shape."""
    if len(obs) != len(horizons):
        raise ValueError(
            f"expected {len(horizons)} horizon observations, got {len(obs)}"
        )
    rows = []
    for o, h in zip(obs, horizons, strict=True):
        target = _d(o["date"])
        base = shift_months(target, -h)
        rows.append(
            {
                "base_month": f"{base.year:04d}-{base.month:02d}",
                "horizon_months": h,
                "target_month": o["date"][:7],
                "value": o["value"],
                "is_past": int(target < today),
            }
        )
    if len({r["base_month"] for r in rows}) != 1:
        raise ValueError(
            f"horizons don't share a base month: {[r['base_month'] for r in rows]}"
        )
    return rows
