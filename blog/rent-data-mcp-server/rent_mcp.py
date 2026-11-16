"""An MCP server for county rent data. Any MCP client (Claude Desktop, Claude Code, Cursor) gets three tools
that compute from Zillow's public rent file; the client's model only reads the results.

Add it to Claude Code:
    claude mcp add rents -- python /full/path/to/rent_mcp.py
"""

from typing import TypedDict

import pandas as pd
from mcp.server.mcpserver import MCPServer

# Zillow Observed Rent Index, county level, smoothed, all homes plus multifamily. Free, no key.
ZORI_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zori/"
    "County_zori_uc_sfrcondomfr_sm_month.csv"
)

mcp = MCPServer("rents")


# Typed returns become the tools' output schemas, so the client's model knows every field it gets back.
class Overview(TypedDict):
    as_of: str
    rising: int
    falling: int
    at_record_high: int
    median_yoy_pct: float


class CountyRow(TypedDict):
    county: str
    rent: float
    yoy_pct: float
    vs_peak_pct: float
    peak_month: str
    as_of: str


class CountyDetail(TypedDict):
    county: str
    rent: int
    yoy_pct_by_month: dict[str, float]


_rents: pd.DataFrame | None = None


def load_rents(source: str = ZORI_URL) -> pd.DataFrame:
    """Monthly rent by county: index (State, RegionName), one column per month-end date."""
    df = pd.read_csv(source)
    months = [c for c in df.columns if c[:2] in ("19", "20")]
    return df.set_index(["State", "RegionName"])[months].dropna(axis=1, how="all")


def rents() -> pd.DataFrame:
    """Download Zillow's file once per server process, on the first tool call."""
    global _rents
    if _rents is None:
        _rents = load_rents()
    return _rents


def county_table(state: str) -> pd.DataFrame:
    """Latest rent, 12-month change, and distance from the all-time high for each county in a state."""
    data = rents()
    s = data.loc[state.upper()].dropna(subset=[data.columns[-1]])
    latest, year_ago = s.columns[-1], s.columns[-13]
    return pd.DataFrame(
        {
            "rent": s[latest].round(0),
            "yoy_pct": (100 * (s[latest] / s[year_ago] - 1)).round(2),
            "vs_peak_pct": (100 * (s[latest] / s.max(axis=1) - 1)).round(2),
            "peak_month": s.idxmax(axis=1).str[:7],
        }
    ).assign(as_of=latest[:7])


@mcp.tool()
def state_overview(state: str) -> Overview:
    """How many of a state's counties are rising, falling, or at a record high, with the median 12-month
    rent change. state is a two-letter code, e.g. FL."""
    t = county_table(state)
    return {
        "as_of": t["as_of"].iloc[0],
        "rising": int((t["yoy_pct"] > 0).sum()),
        "falling": int((t["yoy_pct"] < 0).sum()),
        "at_record_high": int((t["vs_peak_pct"] == 0).sum()),
        "median_yoy_pct": round(float(t["yoy_pct"].median()), 2),
    }


@mcp.tool()
def rank_counties(
    state: str, sort_by: str = "yoy_pct", lowest_first: bool = True, limit: int = 10
) -> list[CountyRow]:
    """Rank a state's counties by rent. sort_by is yoy_pct (12-month change) or vs_peak_pct (percent below
    the county's all-time high). lowest_first=True lists the weakest counties first."""
    t = county_table(state).sort_values(sort_by, ascending=lowest_first).head(limit)
    return t.reset_index(names="county").to_dict("records")


@mcp.tool()
def county_detail(state: str, county: str) -> CountyDetail:
    """One county's latest rent and its 12-month change for each of the last 24 months. county is the
    full name, e.g. 'Lee County'."""
    s = rents().loc[(state.upper(), county)].dropna()
    yoy = (100 * (s / s.shift(12) - 1)).dropna().round(2).tail(24)
    return {
        "county": county,
        "rent": round(float(s.iloc[-1])),
        "yoy_pct_by_month": {d[:7]: v for d, v in yoy.items()},
    }


if __name__ == "__main__":
    mcp.run()  # stdio: the client starts this script and talks to it over stdin/stdout
