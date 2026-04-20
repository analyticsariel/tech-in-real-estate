---
name: redfin-real-estate
description: Reference county-grain housing-market velocity from Redfin (Redfin Data Center, Monthly Market Tracker) for real estate investment decisions. Use this skill whenever a user asks about Redfin data, median sale price, median list price, price per square foot, PPSF, homes sold, pending sales, new listings, active inventory, months of supply, days on market, DOM, sale-to-list ratio, sold above list, price drops, off market in two weeks, listing velocity, bidding pressure, seller capitulation, Hillsborough County, Tampa housing market, or which Monthly Market Tracker columns inform a residential RE decision against Florida and US benchmarks. Maps 14 Redfin metrics across 5 categories (prices, sales_demand, inventory_supply, velocity, negotiation) to investor use-cases. Progressive disclosure — decision playbooks and the full 14-metric reference live in `references/`.
---

# Redfin for Real Estate

## What is Redfin

Redfin Data Center is Redfin's free public data portal — [redfin.com/news/data-center](https://www.redfin.com/news/data-center/). Direct downloads of weekly and monthly TSV feeds covering every US metro, county, city, ZIP, and neighborhood Redfin tracks. For US residential real estate, it's the cleanest free source for sale-side velocity — what closed, what's pending, what got cut, and how fast the market is moving.

This skill targets the **Monthly Market Tracker** specifically, at county grain. Redfin publishes the same TSV schema at national, state, metro, county, city, ZIP, and neighborhood grain — the catalog anchors on Hillsborough County, FL with Florida + US benchmarks (decision #67), but the column set is identical at every level. For tract-level demographics or income context, pair Redfin with Census; for macro rate and affordability backdrop, pair with FRED.

## Bundled resources

| File | When to load |
|---|---|
| `references/metrics.md` | When a user asks about a specific metric, needs a `csv_column` to pull, or any decision playbook below points here. Full 14-metric list, grouped by category, with verbatim rationale each. |
| `references/redfin-datasets.yaml` | When you need richer metadata than `metrics.md` provides — TSV URLs, Python snippets, benchmark geographies, filter logic, fetcher notes. The canonical catalog, 100% field coverage. |

Progressive disclosure rule: start with this file and the category table below. Read `references/metrics.md` only when a specific metric or `csv_column` is actually needed. Read the YAML only when the markdown is insufficient.

## Getting an API key

1. No API key required. Redfin Data Center publishes gzipped TSVs to a public S3 bucket — anyone can pull.
2. No environment variable to set.
3. No dedicated client — `pandas` reads the gzipped TSVs directly from the S3 URL: `pd.read_csv(URL, sep="\t", compression="gzip")`.
4. No published rate limit. Files are large (county tracker ≈ hundreds of MB uncompressed); cache locally if you're iterating.

## Minimal Python example

```python
import pandas as pd

URL = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/county_market_tracker.tsv000.gz"
df = pd.read_csv(URL, sep="\t", compression="gzip", low_memory=False)
df = df[
    (df["TABLE_ID"] == 464)               # Hillsborough County, FL
    & (df["PROPERTY_TYPE_ID"] == -1)      # All Residential aggregate
    & (~df["IS_SEASONALLY_ADJUSTED"])     # non-SA only
].sort_values("PERIOD_END")
print(df[["PERIOD_END", "MEDIAN_SALE_PRICE", "HOMES_SOLD", "MONTHS_OF_SUPPLY"]].tail(12))
```

Swap the `csv_column` set for any metric from `references/metrics.md`. Substitute `state_market_tracker` or `us_national_market_tracker` in the stem for the FL or US benchmark TSV.

## The 5 categories

| Category | Purpose | Count |
|---|---|---|
| `prices` | What homes list and sell for, headline and per-square-foot | 4 |
| `sales_demand` | Closed and pending volume — how much actually traded | 2 |
| `inventory_supply` | New listings, active stock, and months-of-supply balance | 3 |
| `velocity` | How fast listings clear — DOM and the two-week-pending share | 2 |
| `negotiation` | Sale-to-list, above-list share, and price-drop share | 3 |

Total: 14 metrics. See `references/metrics.md` for the full list with `csv_column`s.

## Decision playbooks

Concrete "the user asked X — here's the metric set to pull." Use these as starting points; extend when the question demands it. If a playbook names a metric, `references/metrics.md` has the verbatim rationale.

**"Is the local market still hot or cooling?"**
→ `redfin_median_dom`, `redfin_avg_sale_to_list`, `redfin_sold_above_list`, `redfin_price_drops`
DOM lengthening + sale-to-list dropping below 1.00 + above-list share collapsing + price-drop share rising = the four-signal cooling pattern. Watch them against FL + US to separate local cool-off from national cycle.

**"Where are sellers vs buyers right now?"**
→ `redfin_months_of_supply`, `redfin_inventory`, `redfin_avg_sale_to_list`, `redfin_price_drops`
Months-of-supply is the headline; under four = seller's, over six = buyer's. Inventory direction confirms; sale-to-list and price drops show whether sellers are still holding line or capitulating.

**"How does next month's sale count look?"**
→ `redfin_pending_sales`, `redfin_new_listings`, `redfin_off_market_in_two_weeks`, `redfin_homes_sold`
Pending leads closed by 30–60 days. New listings + off-market-in-two-weeks bracket the supply/demand pulse this month before it shows up in next month's HOMES_SOLD.

**"Are sellers asking too much?"**
→ `redfin_median_list_price`, `redfin_median_sale_price`, `redfin_median_list_ppsf`, `redfin_median_ppsf`, `redfin_price_drops`
List vs sale on both headline and PPSF. Widening list-vs-sale gap + rising price-drop share = local sellers leaning optimistic relative to what the market will actually pay.

**"Is this a bidding war market?"**
→ `redfin_sold_above_list`, `redfin_avg_sale_to_list`, `redfin_off_market_in_two_weeks`, `redfin_months_of_supply`
Above-list share running 10+ points hotter than FL or US + sale-to-list above 1.00 + two-week-pending share elevated + sub-four months supply = bid hot. Price in a cushion or walk earlier.

**"Is supply uncorking?"**
→ `redfin_new_listings`, `redfin_inventory`, `redfin_months_of_supply`, `redfin_price_drops`
New-listings inflow accelerating + active inventory rising + months-of-supply stretching + price-drop share spreading = the supply-loosening sequence in order. Catch it on inflow before the back end shows.

## Gotchas

- **Compute YoY from absolute values, not the `_YOY` columns.** Redfin's published `{COL}_YOY` columns are mixed-semantic — 8 metrics store a ratio, 6 store an absolute delta. The TiRE fetcher derives YoY uniformly from the absolute series and uses native `_YOY` only as a ±0.5pp sanity check (decision #81).
- **TSV headers are UPPER-case.** `MEDIAN_SALE_PRICE`, not `median_sale_price`. Trips up everyone on the first pull.
- **`PROPERTY_TYPE_ID = -1` is the All-Residential aggregate.** The TSV publishes one row per (geo, period, property type, SA flag). Filter to `-1` unless you specifically want SFR (6), Condo (3), Multi-family 2-4 (4), or Townhouse (13).
- **Hillsborough = `TABLE_ID = 464`.** A second Hillsborough exists in NH at TABLE_ID 1886 — always filter explicitly.
- **National TSV publishes both SA and non-SA rows; county and state only publish non-SA.** Filter `IS_SEASONALLY_ADJUSTED = False` on all three so benchmark math stays apples-to-apples.
- **`PRICE_DROPS` history is shorter at county.** Hillsborough starts 2014-02; FL starts 2012-10; US starts 2012-01. Other 13 metrics align at 2012-01 across all three geos. Watch the first-observation alignment if you're indexing.
- **Two old datasets were retired in Sprint 12.** `redfin_weekly_metro_sales` (4-week rolling metro) and `redfin_monthly_city_sales` (city grain) are gone — overlapped Monthly Tracker on a short lag. If you hit a 404 on those keys, re-anchor to county.
- **Files are large.** County Monthly Tracker uncompresses to hundreds of MB. Cache locally if iterating; pull the gzipped form, never the uncompressed one.

## Source of truth

This skill is derived from TiRE's canonical catalog at [agents/data/redfin-datasets.yaml](https://github.com/analyticsariel/tech-in-real-estate-ops/blob/main/agents/data/redfin-datasets.yaml). The YAML is hand-curated; every entry has a `why_it_matters` rationale that feeds both this skill and TiRE's research agents.

When the upstream catalog changes, regenerate `references/metrics.md` and `references/redfin-datasets.yaml`. v1 is hand-curated; build script deferred until drift is observed.
