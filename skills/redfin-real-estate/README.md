# Redfin Real Estate

A Claude skill that maps the **14 Redfin Monthly Market Tracker metrics** a residential investor actually uses — sale + list prices, PPSF, sales counts, pending sales, new + active inventory, months of supply, days on market, sale-to-list, sold-above-list share, price drops, off-market-in-two-weeks — grouped into **5 categories** (prices, sales_demand, inventory_supply, velocity, negotiation) and threaded through **decision playbooks** — so "is bidding pressure breaking yet?" or "are sellers capitulating in this county?" becomes a one-line ask, not a re-paste of the Redfin TSV column dictionary.

## What it does

Redfin Data Center publishes a Monthly Market Tracker TSV at county / state / national grain — the cleanest free feed for how fast a market is moving. For US residential real estate, 14 of those columns carry the prices + velocity + negotiation reads every local investor needs. This skill teaches Claude which 14 metrics matter, the underlying upper-case TSV column for each, the chart mode (yoy_native computed from absolute values, not the publisher's `_YOY` columns — those carry mixed semantics), and how to read each metric against state + national benchmarks. Decision playbooks thread them into supply-loosening, price-cut spread, bidding-pressure shift, and seller-capitulation calls.

Progressive disclosure: the skill loads the 5-category table up front, then pulls the full 14-metric reference or the canonical YAML only when the question demands it.

## Install

```bash
cp -r skills/redfin-real-estate ~/.claude/skills/
```

Then restart Claude Code. The skill auto-triggers when the question mentions Redfin, median sale price, list price, PPSF, homes sold, pending sales, months of supply, days on market, sale-to-list ratio, sold above list, price drops, off market in two weeks, Hillsborough County, or Tampa housing market — no explicit invocation needed.

Prereq: none. Redfin Data Center TSVs are public — no API key, no login.

## What's here

```
redfin-real-estate/
  SKILL.md                              # Claude-facing frontmatter + body
  README.md                             # this file
  references/
    metrics.md                          # full 14-metric reference — dataset_key, csv_column, frequency, unit, verbatim rationale
    redfin-datasets.yaml                # canonical YAML catalog — TSV URLs, Python snippets, benchmark geographies, filter logic, fetcher notes
```

`SKILL.md` carries the pushy description that controls when Claude loads the skill, plus the 5-category table, decision playbooks, a minimal `pandas`-based snippet against the Monthly Market Tracker TSV, and the gotchas (UPPER-case TSV columns, `PROPERTY_TYPE_ID = -1` All Residential aggregate, `IS_SEASONALLY_ADJUSTED = False` filter for apples-to-apples benchmark math, `TABLE_ID = 464` Hillsborough FL, mixed-semantic `_YOY` columns).

`references/metrics.md` is the one-page reference with every Redfin metric, its TSV column name, and the investor rationale verbatim from the catalog. Load it when a specific metric or `csv_column` is needed.

`references/redfin-datasets.yaml` is the canonical catalog — the same shape TiRE uses internally, with 100% field coverage (TSV URLs, county/state/national filter logic, Hillsborough × Florida × USA benchmark configuration, fetcher derivation rules).

## Source of truth

This skill is **mirrored** from `analyticsariel/tech-in-real-estate-ops` (private). The canonical Redfin dataset catalog lives there at `agents/data/redfin-datasets.yaml` and is the upstream of the YAML shipped here. If the private catalog changes, the mirror regenerates.

Live detail page on the TiRE site: <https://techinrealestate.com/skills/redfin-real-estate>.

## License

MIT. Use, fork, adapt — credit TiRE if it helps you, and file issues in this repo if you find rough edges.
