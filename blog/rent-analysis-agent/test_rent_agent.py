"""Offline tests: a tiny fixture instead of Zillow's file, and a scripted fake model instead of an API key.

Run: pytest -q
"""

import pandas as pd
import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolMessage

from rent_agent import build_agent, county_table, make_tools

MONTHS = (
    pd.date_range("2023-01-31", "2026-09-30", freq="ME").strftime("%Y-%m-%d").tolist()
)


@pytest.fixture
def rents() -> pd.DataFrame:
    n = len(MONTHS)
    rows = {
        ("FL", "Lee County"): [
            2000 - 4 * i for i in range(n)
        ],  # peaked at the start, falling since
        ("FL", "Palm Beach County"): [
            2400 + 6 * i for i in range(n)
        ],  # new high every month
        ("FL", "Pinellas County"): [
            1950 + ((i + 1) % 3) for i in range(n)
        ],  # flat, ends level with a year ago
        ("GA", "Fulton County"): [1800 + i for i in range(n)],
    }
    df = pd.DataFrame.from_dict(rows, orient="index", columns=MONTHS)
    df.index = pd.MultiIndex.from_tuples(df.index, names=["State", "RegionName"])
    return df


def test_county_table_matches_hand_math(rents):
    t = county_table(rents, "fl")
    lee = t.loc["Lee County"]
    latest, year_ago, peak = rents.loc[("FL", "Lee County")].iloc[[-1, -13, 0]]
    assert lee["yoy_pct"] == round(100 * (latest / year_ago - 1), 2)
    assert lee["vs_peak_pct"] == round(100 * (latest / peak - 1), 2)
    assert t.loc["Palm Beach County", "vs_peak_pct"] == 0
    assert set(t.index) == {
        "Lee County",
        "Palm Beach County",
        "Pinellas County",
    }  # Georgia excluded


def test_tools(rents):
    overview, rank, detail = make_tools(rents)
    o = overview.invoke({"state": "FL"})
    assert (o["counties"], o["falling"], o["at_record_high"], o["as_of"]) == (
        3,
        1,
        1,
        "2026-09",
    )
    assert (
        rank.invoke({"state": "FL", "sort_by": "vs_peak_pct"})[0]["county"]
        == "Lee County"
    )
    assert (
        len(detail.invoke({"state": "FL", "county": "Lee County"})["yoy_pct_by_month"])
        == 24
    )


class ScriptedModel(GenericFakeChatModel):
    def bind_tools(
        self, tools, **kwargs
    ):  # agents bind tools on startup; the script ignores them
        return self


def test_agent_answers_from_tool_results(rents):
    call = {
        "name": "rank_counties",
        "args": {"state": "FL", "sort_by": "vs_peak_pct"},
        "id": "1",
        "type": "tool_call",
    }
    answer = "Lee County is furthest below its peak."
    model = ScriptedModel(
        messages=iter(
            [AIMessage(content="", tool_calls=[call]), AIMessage(content=answer)]
        )
    )

    result = build_agent(model, rents).invoke(
        {"messages": [{"role": "user", "content": "Where is rent weakest?"}]}
    )

    tool_msg = next(m for m in result["messages"] if isinstance(m, ToolMessage))
    assert "Lee County" in tool_msg.content  # the tool really ran against the data
    assert result["messages"][-1].content == answer
