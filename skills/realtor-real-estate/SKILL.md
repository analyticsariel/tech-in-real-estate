---
name: realtor-real-estate
description: Reference monthly housing-inventory data from Realtor (Realtor.com Research, Monthly Housing Inventory feed) for real estate investment decisions. Use this skill whenever a user asks about Realtor.com data, median listing price, active listings, days on market, pending listings, pending ratio, new listings, total listings, price increases, price reductions, price-cut share, median price per square foot, average listing price, median square feet, listing supply, county-grain inventory, native YoY change, county-vs-state-vs-national benchmarks, monthly housing inventory CSV, RDC inventory metrics, or which Realtor columns inform a residential RE decision. Maps 14 Realtor Monthly Housing Inventory columns across 5 groupings (prices, supply, demand_velocity, pricing_action, mix) to investor use-cases. Progressive disclosure — decision playbooks and the full 14-dataset reference live in `references/`.
---

# Realtor for Real Estate

## What is Realtor

Realtor is Realtor.com's research arm — [realtor.com/research/data](https://www.realtor.com/research/data). Free, no signup, CSV downloads only (no API), refreshed monthly with the Monthly Housing Inventory feed plus a few weekly and hotness reports we don't track here. For US residential real estate, it's the authoritative single stop for county-grain listing-side reads — list prices, active and pending counts, days on market, and price-cut behavior — pulled from the MLS pipeline that powers the consumer site.

Realtor's Monthly Housing Inventory ships at national, state, metro, county, and ZIP grain — and county is the finest cut that fills reliably across all 14 columns. For tract-level demand reads (income, tenure, vacancy), pair with Census ACS. For weekly velocity or sale-side pricing, pair with Redfin. For long-history ZIP-level home values, pair with Zillow's ZHVI.

## Bundled resources

| File | When to load |
|---|---|
| `references/metrics.md` | When a user asks about a specific column, needs a `csv_column` to pull, or any decision playbook below points here. Full 14-column list, grouped by category, with verbatim rationale each. |
| `references/realtor-datasets.yaml` | When you need richer metadata than `metrics.md` provides — CSV URLs, YoY column names, benchmark geographies, copy-pasteable Python snippets. The canonical catalog, 100% field coverage. |

Progressive disclosure rule: start with this file and the category table below. Read `references/metrics.md` only when a specific column or `csv_column` is actually needed. Read the YAML only when the markdown is insufficient.

## Getting an API key

1. No API key required. The Monthly Housing Inventory feed ships as public CSVs on S3 — pull them with `pandas.read_csv` or `requests`.
2. No environment variable to set. The catalog's `csv_url` fields are the URLs to hit directly.
3. No dedicated client. `pip install pandas` covers every pull; `requests` works too if you want raw bytes.
4. No rate limit published. The CSVs are static monthly snapshots — pull once a month, cache locally, don't hammer the host.

## Minimal Python example

```python
import pandas as pd

# Median listing price — Hillsborough County, FL
url = "https://econdata.s3-us-west-2.amazonaws.com/Reports/Core/RDC_Inventory_Core_Metrics_County_History.csv"
df = pd.read_csv(url)
df = df[df["county_fips"] == 12057]
df["date"] = pd.to_datetime(df["month_date_yyyymm"], format="%Y%m") + pd.offsets.MonthEnd(0)
df = df.sort_values("date")
print(df[["date", "median_listing_price", "median_listing_price_yy"]].tail(12))
```

Swap `median_listing_price` for any `csv_column` from `references/metrics.md`. Swap `_County_` for `_State_` (filter on `state_id`) or `_Country_` (no filter — one row per month) for the state/national CSVs.

## The 5 groupings

| Grouping | Purpose | Count |
|---|---|---|
| `prices` | What sellers are asking: medians, per-sqft, mean | 3 |
| `supply` | Listings on the market: active, new, total | 3 |
| `demand_velocity` | How fast it's moving: DOM, pending, pending ratio | 3 |
| `pricing_action` | Seller confidence vs. buyer leverage: price increases and cuts, count + share | 4 |
| `mix` | Composition of what's listed: median square feet | 1 |

Total: 14 columns. See `references/metrics.md` for the full list with `csv_column`s and rationale.

## Decision playbooks

Concrete "the user asked X — here's the column set to pull." Use these as starting points; extend when the question demands it. If a playbook names a column, `references/metrics.md` has the verbatim rationale.

**"Is supply tightening or loosening here?"**
→ `active_listing_count`, `new_listing_count`, `total_listing_count`, `median_days_on_market`
Active is the live snapshot; new is the inflow; total = active + pending (separates real supply from churn); DOM is the absorption read. Run them together against state + national to see if local supply is moving with the cycle or against it.

**"Where's negotiating leverage right now?"**
→ `price_reduced_share`, `price_increased_share`, `pending_ratio`, `median_days_on_market`
Share-form price-cut and price-increase columns smooth out inventory swings; pending ratio above 1.0 says deals-in-motion outnumber for-sale homes (hot market). DOM stretching while cuts spread = buyer leverage building.

**"Are Tampa prices a premium or a discount?"**
→ `median_listing_price`, `median_listing_price_per_square_foot`, `average_listing_price`, `median_square_feet`
Median is the headline; per-sqft controls for size-mix shifts; average vs. median gap reads the luxury-tail influence; median square feet flags whether a mix change is driving the headline. Benchmark all four against FL + US.

**"Is demand running ahead of or behind closings?"**
→ `pending_listing_count`, `pending_ratio`, `median_days_on_market`, `new_listing_count`
Pending count is the 30–60 day leading indicator of closed sales. Pending ratio normalizes for inventory. DOM and new listings frame whether the pending build is real demand or just fresh supply moving fast.

**"Are sellers giving up pricing power?"**
→ `price_reduced_count`, `price_reduced_share`, `price_increased_count`, `price_increased_share`
Watch the share lines for cycle turns — the count versions move with raw inventory. When Hillsborough's reduced-share runs above FL and US while increased-share runs below, sellers are blinking first locally.

**"Quick monthly Tampa pulse — three columns to scan?"**
→ `median_listing_price`, `active_listing_count`, `median_days_on_market`
The three TiRE surfaces as the headline Realtor metrics. Price level, supply level, velocity — every other column in the catalog adds nuance to one of these three.

## Gotchas

- **CSV-only, no API.** The Monthly Housing Inventory feed is a public S3 CSV. No tokens, no JSON endpoint, no historical snapshots beyond the rolling file. Cache locally if you need a point-in-time read.
- **Three separate CSVs by grain.** County, state, and national each live in their own file (`_County_`, `_State_`, `_Country_` in the URL stem). The fetcher in `agents/sources/realtor.py` does the substitution; if you're pulling raw, swap the stem yourself.
- **Native YoY columns.** Every metric ships with a paired `_yy` column (decimal float — multiply by 100 for percent). Use these directly per decision #72; don't recompute YoY off the level series.
- **Country CSV has no filter column.** It's one row per month nationally. The county and state CSVs need filtering on `county_fips` (int) or `state_id` (string like `"FL"`).
- **County FIPS as integer.** `county_fips` in the CSV is an int, not a zero-padded string. Hillsborough is `12057` (not `"12057"`); cast accordingly when filtering.
- **Monthly cadence, ~3 week lag.** The previous month's data drops mid-month. Don't expect intra-month freshness — Realtor isn't Redfin's weekly feed.
- **History starts 2016-07.** All three CSVs ship 2016-07 onward. ~117 months as of 2026-04. Anything earlier needs a different source.
- **Two dropped Sprint 4 datasets are gone for good.** `realtor_hotness_monthly_county` and `realtor_weekly_national` were cut in Sprint 9 (decision #73) — don't propose them. Their columns are either redundant with Monthly Inventory or national-only YoY-only, neither of which earns a /metric page.

## Source of truth

This skill is derived from TiRE's canonical catalog at [agents/data/realtor-datasets.yaml](https://github.com/analyticsariel/tech-in-real-estate-ops/blob/main/agents/data/realtor-datasets.yaml). The YAML is hand-curated; every entry has a `why_it_matters` rationale that feeds both this skill and TiRE's research agents.

When the upstream catalog changes, regenerate `references/metrics.md` and `references/realtor-datasets.yaml`. v1 is hand-curated; build script deferred until drift is observed.
