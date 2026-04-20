# Zillow Real Estate

A Claude skill that maps **33 Zillow Research headlines + 119 variants = 152 catalogued cuts** a residential investor actually uses — ZHVI, ZHVF, ZORI, ZORDI, ZORF, PITI carry-cost, for-sale and pending listings flow, sale prices and ratios, DOM, price cuts, Market Heat Index, new construction, affordability — grouped into **11 categories** (home_values, mortgage_carry, rents, inventory_listings, prices_sales, negotiation, velocity, price_cuts, market_heat, new_construction, affordability) and threaded through **decision playbooks** — so "is ZIP-level rent growth pulling away from value?" or "is bidding pressure breaking in this metro?" becomes a one-line ask, not a re-paste of the Zillow CSV index.

## What it does

Zillow Research publishes the deepest free home-value (ZHVI) and rent (ZORI) series available, plus 31 other headline indices spanning mortgages, listings, sales, velocity, price cuts, market heat, new construction, and affordability — at national, state, metro, county, city, ZIP, and neighborhood grain. This skill teaches Claude which 33 headlines matter for a leveraged RE decision, which of the 119 variant cuts (Single-Family vs Condo, raw vs smoothed/SA, top vs bottom tier) to reach for, the canonical CSV URL stem for each, and how to read ZIP-level moves against the long-run state and metro benchmarks. Decision playbooks thread them into the calls an investor actually makes — value-vs-rent divergence, carry-cost reality, bidding-pressure shifts, affordability gates.

Progressive disclosure: the skill loads the 11-category headline table up front, then pulls the full 33-headline reference (with variant lists) or the canonical YAML only when the question demands it.

## Install

```bash
cp -r skills/zillow-real-estate ~/.claude/skills/
```

Then restart Claude Code. The skill auto-triggers when the question mentions ZHVI, ZHVF, ZORI, ZORDI, ZORF, PITI, for-sale inventory, days to pending, price cuts, Market Heat Index, ZIP-level home values, or metro rent comps — no explicit invocation needed.

Prereq: none. Zillow Research CSVs are public — no API key, no login.

## What's here

```
zillow-real-estate/
  SKILL.md                              # Claude-facing frontmatter + body
  README.md                             # this file
  references/
    metrics.md                          # full 33-headline reference (with 119 variant cuts) — key, frequency, unit, verbatim rationale per headline
    zillow-datasets.yaml                # canonical YAML catalog — CSV URLs, geo levels, variants, benchmark geographies, Python snippets
```

`SKILL.md` carries the pushy description that controls when Claude loads the skill, plus the 11-category headline table, decision playbooks, a minimal `pandas`-based snippet against the ZHVI metro CSV, and the gotchas (RegionID is the only meta column guaranteed across all CSVs, smoothed-SA vs raw cut codes, geo-level coverage varies per cut, Tampa MSA RegionID 395148, ZIP codes as strings not ints, `_All Homes` vs `_SFR` aggregation differences).

`references/metrics.md` is the one-page reference with every Zillow headline grouped by category, its CSV URL stem, and the investor rationale verbatim from the catalog. Variant cuts are listed under each headline as "Also available as..." sub-items. Load it when a specific cut or RegionID is needed.

`references/zillow-datasets.yaml` is the canonical catalog — the same shape TiRE uses internally, with 100% field coverage (CSV URLs per cut, geo-level coverage maps, Tampa MSA × Florida × USA benchmark configuration, fetcher derivation rules).

## Source of truth

This skill is **mirrored** from `analyticsariel/tech-in-real-estate-ops` (private). The canonical Zillow dataset catalog lives there at `agents/data/zillow-datasets.yaml` and is the upstream of the YAML shipped here. If the private catalog changes, the mirror regenerates.

Live detail page on the TiRE site: <https://techinrealestate.com/skills/zillow-real-estate>.

## License

MIT. Use, fork, adapt — credit TiRE if it helps you, and file issues in this repo if you find rough edges.
