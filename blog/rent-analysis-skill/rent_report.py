"""Compare county rents from Zillow's ZORI file and print JSON for Claude to read.

Usage:
    python rent_report.py FL "Lee" "Palm Beach"
    python rent_report.py FL "Lee" --csv County_zori.csv   # use a local copy
"""

from __future__ import annotations

import argparse
import json
import re
import sys

import pandas as pd

ZORI_URL = "https://files.zillowstatic.com/research/public_csvs/zori/County_zori_uc_sfrcondomfr_sm_month.csv"
DATE_COL = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_rents(source: str = ZORI_URL) -> pd.DataFrame:
    """Read Zillow's county rent CSV into one row per county: county, state, then one column per month."""
    raw = pd.read_csv(source)
    state_col = "State" if "State" in raw.columns else "StateName"
    dates = [c for c in raw.columns if DATE_COL.match(c)]
    return raw[["RegionName", state_col, *dates]].rename(columns={"RegionName": "county", state_col: "state"})


def county_table(rents: pd.DataFrame, state: str) -> tuple[pd.DataFrame, str]:
    """Latest rent, 12-month change and distance from the all-time high for each county in a state."""
    in_state = rents[rents["state"].str.upper() == state.upper()].set_index("county").drop(columns="state")
    if in_state.empty:
        raise ValueError(f"no counties found for state {state!r}")
    in_state = in_state.dropna(subset=[in_state.columns[-1]])
    latest = in_state.columns[-1]
    months = pd.PeriodIndex(pd.to_datetime(in_state.columns), freq="M")
    try:
        year_ago = in_state.columns[months.get_loc(months[-1] - 12)]
    except KeyError:
        raise ValueError("the file has no month 12 months before the latest one") from None
    table = pd.DataFrame(
        {
            "rent": in_state[latest].round(0),
            "yoy_dollars": (in_state[latest] - in_state[year_ago]).round(0),
            "yoy_pct": (100 * (in_state[latest] / in_state[year_ago] - 1)).round(2),
            "vs_peak_pct": (100 * (in_state[latest] / in_state.max(axis=1) - 1)).round(2),
            "peak_month": in_state.idxmax(axis=1).str[:7],
        }
    )
    return table, latest[:7]


def _key(name: str) -> str:
    return name.strip().lower().removesuffix(" county")


def _num(value) -> float | None:
    return None if pd.isna(value) else float(value)


def compare(rents: pd.DataFrame, state: str, names: list[str]) -> dict:
    """Compare the named counties with each other and with the rest of the state."""
    table, as_of = county_table(rents, state)
    ranks = table["yoy_pct"].rank(ascending=False, method="min")
    lookup = {_key(county): county for county in table.index}
    found, not_found = [], []
    for name in names:
        county = lookup.get(_key(name))
        if county is None:
            not_found.append(name)
            continue
        row = table.loc[county]
        found.append(
            {
                "county": county,
                "rent": _num(row["rent"]),
                "yoy_dollars": _num(row["yoy_dollars"]),
                "yoy_pct": _num(row["yoy_pct"]),
                "yoy_rank": None if pd.isna(ranks[county]) else int(ranks[county]),
                "vs_peak_pct": _num(row["vs_peak_pct"]),
                "peak_month": str(row["peak_month"]),
            }
        )
    return {
        "state": state.upper(),
        "as_of": as_of,
        "counties_ranked": int(table["yoy_pct"].notna().sum()),
        "state_median_yoy_pct": round(float(table["yoy_pct"].median()), 2),
        "counties": found,
        "not_found": not_found,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare county rents from Zillow's ZORI file.")
    parser.add_argument("state", help="two-letter state code, e.g. FL")
    parser.add_argument("counties", nargs="+", help='county names, e.g. "Lee" "Palm Beach"')
    parser.add_argument("--csv", default=ZORI_URL, help="path or URL of the ZORI county CSV")
    args = parser.parse_args(argv)
    try:
        report = compare(load_rents(args.csv), args.state, args.counties)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
