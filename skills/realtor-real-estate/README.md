# Realtor Real Estate

A Claude skill that maps the **14 Realtor.com Monthly Housing Inventory columns** a residential investor actually uses — list prices, active and pending counts, days on market, price-cut share, price-per-sqft, mix — grouped into **5 groupings** (prices, supply, demand velocity, pricing action, mix) and threaded through **decision playbooks** — so "is this county loosening or tightening on supply?" or "are sellers cutting yet?" becomes a one-line ask, not a re-paste of the RDC column dictionary.

## What it does

Realtor.com publishes a monthly CSV per county (and per state, per country) with native year-over-year columns already computed. For US residential real estate, 14 of those columns carry the supply, list-price, and velocity read every local investor needs. This skill teaches Claude which 14 columns matter, the underlying CSV column name and `_yy` partner for each, the chart mode (yoy_native), and how to read each column against state + national benchmarks rather than in isolation. Decision playbooks thread them into the questions an investor actually asks before writing an offer — supply-trend, price-cut spread, days-to-sale, mix shift.

Progressive disclosure: the skill loads the 5-grouping table up front, then pulls the full 14-column reference or the canonical YAML only when the question demands it.

## Install

```bash
cp -r skills/realtor-real-estate ~/.claude/skills/
```

Then restart Claude Code. The skill auto-triggers when the question mentions Realtor.com data, median listing price, active listings, days on market, pending listings, pending ratio, price-cut share, price per square foot, monthly housing inventory CSV, or county-grain RDC metrics — no explicit invocation needed.

Prereq: none. Realtor.com Research CSVs are public — no API key, no login.

## What's here

```
realtor-real-estate/
  SKILL.md                              # Claude-facing frontmatter + body
  README.md                             # this file
  references/
    metrics.md                          # full 14-column reference — key, csv_column, frequency, unit, verbatim rationale
    realtor-datasets.yaml               # canonical YAML catalog — CSV columns, _yy partners, benchmark geographies, fetcher notes
```

`SKILL.md` carries the pushy description that controls when Claude loads the skill, plus the 5-grouping table, decision playbooks, a minimal `pandas`-based snippet against the Monthly Housing Inventory CSV, and the gotchas (yoy_native chart mode, county/state/country file-stem derivation, `_yy` decimal-vs-percent convention, single-county Hillsborough framing vs MSA).

`references/metrics.md` is the one-page reference with every Realtor column, its CSV column name, and the investor rationale verbatim from the catalog. Load it when a specific column or `_yy` partner is needed.

`references/realtor-datasets.yaml` is the canonical catalog — the same shape TiRE uses internally, with 100% field coverage (CSV column + `_yy` column, Hillsborough × Florida × USA benchmark configuration, fetcher derivation rules).

## Source of truth

This skill is **mirrored** from `analyticsariel/tech-in-real-estate-ops` (private). The canonical Realtor dataset catalog lives there at `agents/data/realtor-datasets.yaml` and is the upstream of the YAML shipped here. If the private catalog changes, the mirror regenerates.

Live detail page on the TiRE site: <https://techinrealestate.com/skills/realtor-real-estate>.

## License

MIT. Use, fork, adapt — credit TiRE if it helps you, and file issues in this repo if you find rough edges.
