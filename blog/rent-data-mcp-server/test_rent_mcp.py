"""Offline tests: a tiny fixture instead of Zillow's file, and a real MCP client connected in-process.

Run: pytest -q
"""

import pandas as pd
import pytest
from mcp.client import Client

import rent_mcp

MONTHS = (
    pd.date_range("2023-01-31", "2026-09-30", freq="ME").strftime("%Y-%m-%d").tolist()
)


@pytest.fixture(autouse=True)
def fixture_rents(monkeypatch):
    n = len(MONTHS)
    rows = {
        ("FL", "Lee County"): [
            2000 - 4 * i for i in range(n)
        ],  # falling since the start
        ("FL", "Palm Beach County"): [
            2400 + 6 * i for i in range(n)
        ],  # new high every month
        ("GA", "Fulton County"): [1800 + i for i in range(n)],
    }
    df = pd.DataFrame.from_dict(rows, orient="index", columns=MONTHS)
    df.index = pd.MultiIndex.from_tuples(df.index, names=["State", "RegionName"])
    monkeypatch.setattr(rent_mcp, "_rents", df)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_server_lists_the_three_tools():
    async with Client(rent_mcp.mcp) as client:
        names = {t.name for t in (await client.list_tools()).tools}
    assert names == {"state_overview", "rank_counties", "county_detail"}


@pytest.mark.anyio
async def test_tools_answer_over_mcp():
    async with Client(rent_mcp.mcp) as client:
        overview = await client.call_tool("state_overview", {"state": "FL"})
        ranked = await client.call_tool(
            "rank_counties", {"state": "FL", "sort_by": "vs_peak_pct"}
        )
    o = overview.structured_content
    assert (o["rising"], o["falling"], o["at_record_high"], o["as_of"]) == (
        1,
        1,
        1,
        "2026-09",
    )
    assert ranked.structured_content["result"][0]["county"] == "Lee County"
