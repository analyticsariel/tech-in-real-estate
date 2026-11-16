"""Offline tests: fixture data in Zillow's CSV layout, no network, no keys."""

import json
import re
from pathlib import Path

import pandas as pd
import pytest

import rent_report

SKILL = Path(__file__).parent / "SKILL.md"
MONTHS = [d.strftime("%Y-%m-%d") for d in pd.date_range("2025-08-31", periods=14, freq="ME")]

# 14 months, 2025-08 through 2026-09. Year-ago month is the second value.
SERIES = {
    ("Lee County", "FL"): [2000, 2100, 2200, 2150] + [2100 - 20 * i for i in range(10)],
    ("Palm Beach County", "FL"): [2500 + 25 * i for i in range(14)],
    ("Collier County", "FL"): [3000] * 14,
    ("Hillsborough County", "FL"): [2000 + 10 * i for i in range(14)],
    ("Pasco County", "FL"): [1800 + 5 * i for i in range(14)],
    ("Glades County", "FL"): [1500] * 13 + [None],  # no latest month: dropped
    ("Fulton County", "GA"): [1600] * 14,
}


@pytest.fixture
def csv_path(tmp_path):
    rows = []
    for i, ((county, state), values) in enumerate(SERIES.items()):
        meta = {
            "RegionID": i,
            "SizeRank": i,
            "RegionName": county,
            "RegionType": "county",
            "StateName": state,
            "State": state,
            "Metro": "",
            "StateCodeFHFA": 0,
            "MunicipalCodeFHFA": 0,
        }
        rows.append({**meta, **dict(zip(MONTHS, values))})
    path = tmp_path / "zori.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return str(path)


@pytest.fixture
def rents(csv_path):
    return rent_report.load_rents(csv_path)


def test_load_rents_keeps_only_county_state_and_months(rents):
    assert list(rents.columns) == ["county", "state", *MONTHS]


def test_county_table_matches_hand_math(rents):
    table, as_of = rent_report.county_table(rents, "fl")
    lee, palm = table.loc["Lee County"], table.loc["Palm Beach County"]
    assert as_of == "2026-09"
    assert (lee["rent"], lee["yoy_dollars"]) == (1920, -180)
    assert lee["yoy_pct"] == pytest.approx(-8.57, abs=0.01)
    assert lee["vs_peak_pct"] == pytest.approx(-12.73, abs=0.01)
    assert lee["peak_month"] == "2025-10"
    assert palm["yoy_pct"] == pytest.approx(11.88, abs=0.01)
    assert palm["vs_peak_pct"] == 0
    assert "Glades County" not in table.index
    assert "Fulton County" not in table.index


def test_compare_ranks_matches_names_and_reports_misses(rents):
    report = rent_report.compare(rents, "FL", ["lee", "Palm Beach County", "Glades"])
    lee, palm = report["counties"]
    assert (palm["yoy_rank"], lee["yoy_rank"]) == (1, 5)
    assert report["counties_ranked"] == 5
    assert report["state_median_yoy_pct"] == pytest.approx(3.32, abs=0.01)
    assert report["not_found"] == ["Glades"]
    assert report["as_of"] == "2026-09"


def test_unknown_state_raises(rents):
    with pytest.raises(ValueError, match="no counties"):
        rent_report.compare(rents, "ZZ", ["Lee"])


def test_cli_prints_json(csv_path, capsys):
    assert rent_report.main(["FL", "Lee", "--csv", csv_path]) == 0
    assert json.loads(capsys.readouterr().out)["counties"][0]["county"] == "Lee County"


def test_cli_reports_a_missing_file(tmp_path, capsys):
    assert rent_report.main(["FL", "Lee", "--csv", str(tmp_path / "nope.csv")]) == 1
    assert "error" in capsys.readouterr().err


def test_skill_file_is_well_formed():
    _, front, body = SKILL.read_text().split("---\n", 2)
    meta = dict(line.split(": ", 1) for line in front.strip().splitlines())
    assert re.fullmatch(r"[a-z0-9-]{1,64}", meta["name"])
    assert 0 < len(meta["description"]) <= 1024
    assert "Use when" in meta["description"]
    assert "rent_report.py" in body


def test_skill_only_names_fields_the_script_returns(rents):
    report = rent_report.compare(rents, "FL", ["Lee"])
    emitted = set(report) | set(report["counties"][0])
    named = set(re.findall(r"`([a-z_]+)`", SKILL.read_text()))
    assert named <= emitted
