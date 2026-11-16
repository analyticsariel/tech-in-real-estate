"""A rent-analysis agent. The tools do the math on Zillow's public rent data; the model only reads results.

Run it:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=...
    python rent_agent.py "Where are Florida rents falling, and is there a pattern?"
"""

from __future__ import annotations

import sys

import pandas as pd
from langchain.agents import create_agent
from langchain.tools import tool

# Zillow Observed Rent Index, county level, smoothed, all homes plus multifamily. Free, no key.
ZORI_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zori/"
    "County_zori_uc_sfrcondomfr_sm_month.csv"
)

SYSTEM_PROMPT = """You analyze rental markets for people who own a few rental properties.
- Every number you state comes from a tool result. Never calculate, estimate or round beyond the tool's output.
- Say which month the data runs through.
- Look for a pattern across counties (geography, size, timing) and say plainly what the data can't explain.
- End with what an owner should do differently because of the answer."""


def load_rents(source: str = ZORI_URL) -> pd.DataFrame:
    """Monthly rent by county: index (State, RegionName), one column per month-end date."""
    df = pd.read_csv(source)
    months = [c for c in df.columns if c[:2] in ("19", "20")]
    return df.set_index(["State", "RegionName"])[months].dropna(axis=1, how="all")


def county_table(rents: pd.DataFrame, state: str) -> pd.DataFrame:
    """Latest rent, 12-month change, and distance from the all-time high for each county in a state."""
    s = rents.loc[state.upper()].dropna(subset=[rents.columns[-1]])
    latest, year_ago = s.columns[-1], s.columns[-13]
    return pd.DataFrame(
        {
            "rent": s[latest].round(0),
            "yoy_pct": (100 * (s[latest] / s[year_ago] - 1)).round(2),
            "vs_peak_pct": (100 * (s[latest] / s.max(axis=1) - 1)).round(2),
            "peak_month": s.idxmax(axis=1).str[:7],
        }
    ).assign(as_of=latest[:7])


def make_tools(rents: pd.DataFrame) -> list:
    @tool
    def state_overview(state: str) -> dict:
        """How many of a state's counties are rising, falling, or at a record high, with the median 12-month change.
        state is a two-letter code, e.g. FL."""
        t = county_table(rents, state)
        return {
            "as_of": t["as_of"].iloc[0],
            "counties": len(t),
            "rising": int((t["yoy_pct"] > 0).sum()),
            "falling": int((t["yoy_pct"] < 0).sum()),
            "at_record_high": int((t["vs_peak_pct"] == 0).sum()),
            "median_yoy_pct": round(float(t["yoy_pct"].median()), 2),
        }

    @tool
    def rank_counties(
        state: str, sort_by: str = "yoy_pct", lowest_first: bool = True, limit: int = 10
    ) -> list[dict]:
        """Rank a state's counties. sort_by is yoy_pct (12-month rent change) or vs_peak_pct (percent below the
        county's all-time high). lowest_first=True lists the weakest counties first."""
        t = (
            county_table(rents, state)
            .sort_values(sort_by, ascending=lowest_first)
            .head(limit)
        )
        return t.reset_index(names="county").to_dict("records")

    @tool
    def county_detail(state: str, county: str) -> dict:
        """One county's latest rent and its 12-month change for each of the last 24 months. county is the
        full name, e.g. 'Lee County'."""
        s = rents.loc[(state.upper(), county)].dropna()
        yoy = (100 * (s / s.shift(12) - 1)).dropna().round(2).tail(24)
        return {
            "county": county,
            "rent": round(float(s.iloc[-1])),
            "yoy_pct_by_month": {d[:7]: v for d, v in yoy.items()},
        }

    return [state_overview, rank_counties, county_detail]


def build_agent(model, rents: pd.DataFrame | None = None):
    """model: a chat model or a provider string such as 'anthropic:claude-sonnet-5-5'."""
    rents = load_rents() if rents is None else rents
    return create_agent(
        model=model, tools=make_tools(rents), system_prompt=SYSTEM_PROMPT
    )


if __name__ == "__main__":
    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Where are Florida rents falling, and is there a pattern?"
    )
    agent = build_agent("anthropic:claude-sonnet-5-5")
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    print(result["messages"][-1].content)
