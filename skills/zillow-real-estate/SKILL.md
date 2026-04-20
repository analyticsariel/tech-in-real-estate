---
name: zillow-real-estate
description: Reference US home values, rents, listings flow, sales velocity, price cuts, and affordability from Zillow (Zillow Research public CSVs) for real estate investment decisions. Use this skill whenever a user asks about ZHVI, Zillow Home Value Index, ZHVF, ZORI, ZORDI, ZORF, PITI, for-sale inventory, newly pending listings, sale-to-list ratio, days to pending, price-cut share, Zillow Market Heat Index, new construction prices, years to save, ZIP-level home values, metro rent comps, or which Zillow Research cuts inform a residential RE decision. Maps 33 Zillow headlines + 119 variants across 11 categories (home_values, mortgage_carry, rents, inventory_listings, prices_sales, negotiation, velocity, price_cuts, market_heat, new_construction, affordability) to investor use-cases. Progressive disclosure — decision playbooks and the full 33-headline reference live in `references/`.
---

# Zillow for Real Estate

## What is Zillow

Zillow Research is Zillow's public data program — [zillow.com/research/data](https://www.zillow.com/research/data/). Free, no signup, ~150 monthly CSVs covering home values, forecasts, rents, listings flow, sales, days-on-market, price cuts, market heat, new construction, and affordability. For US residential real estate, it's the authoritative single stop for ZIP-level home values (ZHVI), metro-level rent benchmarks (ZORI), and the listings-side velocity reads no government source publishes monthly.

Zillow Research goes ZIP-deep on home values and metro-deep on most listings/sales/affordability cuts. For below-ZIP grain (tract, block-group) on demographics and tenure, pair with Census ACS — Zillow doesn't publish at that resolution.

## Bundled resources

| File | When to load |
|---|---|
| `references/metrics.md` | When a user asks about a specific Zillow series, needs a `dataset_key` or CSV URL to pull, or any decision playbook below points here. Full 33-headline list (with the 119 variant cuts surfaced per headline), grouped by category, with verbatim rationale each. |
| `references/zillow-datasets.yaml` | When you need richer metadata than `metrics.md` provides — full variant URLs, tags, geo levels, featured-geo + benchmark configs, copy-pasteable Python snippets per series. The canonical catalog, 100% field coverage. |

Progressive disclosure rule: start with this file and the category table below. Read `references/metrics.md` only when a specific series, variant, or CSV URL is actually needed. Read the YAML only when the markdown is insufficient.

## Getting an API key

1. No API key required. Zillow Research publishes static CSVs at `files.zillowstatic.com/research/public_csvs/...` — `pd.read_csv(url)` is the entire client.
2. No env var to set, no signup, no rate limit published. Be a good neighbor: cache locally, don't hammer the same URL on a loop.
3. Refresh cadence is monthly for most series, weekly for a handful of variants (look for `_week.csv` vs `_month.csv` in the URL).
4. Terms of use: research/non-commercial OK, commercial redistribution requires permission. Cite Zillow Research when you publish.

## Minimal Python example

```python
import pandas as pd

# ZHVI All Homes (Smoothed, SA, Mid-Tier) — Tampa MSA (RegionID 395148)
url = (
    "https://files.zillowstatic.com/research/public_csvs/zhvi/"
    "Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)
df = pd.read_csv(url)
meta = ["RegionID", "SizeRank", "RegionName", "RegionType", "StateName"]
tampa = (
    df[df["RegionID"] == 395148]
    .melt(id_vars=[c for c in df.columns if c in meta],
          var_name="date", value_name="zhvi")
    .dropna(subset=["zhvi"])
)
print(tampa[["date", "zhvi"]].tail(12))
```

Swap the URL for any CSV from `references/metrics.md` (or the `csv_url` / `variants[].csv_url` fields in the YAML). Featured geography across the catalog is Tampa-St. Petersburg-Clearwater MSA (RegionID 395148), benchmarked against Florida (RegionID 14) + United States (RegionID 102001).

## The 11 categories

| Category | Purpose | Headlines | Variants |
|---|---|---|---|
| `home_values` | ZHVI level + ZHVF growth forecast | 2 | 11 |
| `mortgage_carry` | What the typical home actually costs to carry monthly | 2 | 4 |
| `rents` | ZORI level, ZORDI demand, ZORF forecast | 3 | 9 |
| `inventory_listings` | For-sale inventory, new listings, newly pending | 3 | 13 |
| `prices_sales` | List, sale, mean, count, total transaction value | 5 | 21 |
| `negotiation` | Sale-to-list ratio + above/below-list share | 2 | 14 |
| `velocity` | Days to pending + days to close | 2 | 14 |
| `price_cuts` | Share of listings with a cut + dollar/percent depth | 3 | 33 |
| `market_heat` | Zillow's composite buyer/balanced/seller score | 1 | 0 |
| `new_construction` | Sales count + price (median, mean, $/sqft) for new builds | 4 | 0 |
| `affordability` | Income needed, affordable price, years to save, threshold indices | 6 | 0 |

Total: 33 headlines + 119 variants = 152 cuts. See `references/metrics.md` for the full list with `dataset_key`s, CSV URLs, and the per-headline "Also available as..." variant lists.

## Decision playbooks

Concrete "the user asked X — here's the Zillow series set to pull." Use these as starting points; extend when the question demands it. If a playbook names a series, `references/metrics.md` has the verbatim rationale.

**"What's a typical home worth here, and where's it headed?"**
→ `zillow_zhvi`, `zillow_zhvf`, `zillow_median_sale_price`
ZHVI is the defensible "typical home value." ZHVF is the directional forecast. Median sale price is the noisier transaction read — never use it without ZHVI alongside.

**"Is this market a buyer's or seller's right now?"**
→ `zillow_market_heat_index`, `zillow_sale_to_list_ratio`, `zillow_share_sold_above_below_list`, `zillow_share_price_cut`
Heat index is the composite. Sale-to-list and above-list share read negotiation directly. Price-cut share is the early-warning that sellers are blinking before the ratios move.

**"How fast is supply turning, and is it tightening or loosening?"**
→ `zillow_for_sale_inventory`, `zillow_new_listings`, `zillow_newly_pending_listings`, `zillow_days_to_pending`
Inventory is the level. New listings vs newly pending tells you whether supply is growing because nothing sells or because sellers are listing. Days to pending is the velocity confirm.

**"Can a typical buyer afford anything in this metro?"**
→ `zillow_new_homeowner_affordability`, `zillow_new_homeowner_income_needed`, `zillow_affordable_home_price`, `zillow_years_to_save`
Affordability index is the share-of-income read against Zillow's 30% threshold. Income needed and affordable price work the same math from opposite ends. Years to save is the down-payment angle.

**"What's a fair rent ask, and where's rent demand going?"**
→ `zillow_zori`, `zillow_zordi`, `zillow_zorf`, `zillow_new_renter_affordability`
ZORI is the rent benchmark. ZORDI leads ZORI by months — demand climbs first, rent follows. ZORF is the national forecast. Renter affordability checks whether your ask is breaching the 30% threshold for local renters.

**"Is the new-construction market diverging from resale here?"**
→ `zillow_new_construction_median_sale_price`, `zillow_new_construction_median_price_per_sqft`, `zillow_new_construction_sales_count`, `zillow_median_sale_price`
Builder vs resale median tells you the new-build premium (or discount). Price-per-sqft normalizes for builders shrinking product. Sales count says whether builders are actually moving inventory.

## Gotchas

- **Smoothed vs raw, seasonally-adjusted vs not.** Most headline series default to smoothed + SA (`_sm_sa_month.csv`); raw and non-SA cuts ship as variants. Don't compare a smoothed-SA series against a raw one without normalizing — the smoothing strips real moves alongside noise.
- **CSV columns are dates, not values.** Every Zillow CSV is wide-format: meta columns (`RegionID`, `SizeRank`, `RegionName`, `RegionType`, `StateName`) plus one column per month/week. Always `melt()` after filtering on `RegionID`.
- **Geo levels vary per series.** ZHVI ships at national/state/metro/county/city/ZIP/neighborhood. Many sales/listings cuts are national + metro only. Check `geo_levels` in the YAML before assuming ZIP coverage.
- **Tier suffixes encode price band.** `tier_0.33_0.67` = mid-tier (33rd–67th percentile, the headline). `tier_0.0_0.33` = bottom tier. `tier_0.67_1.0` = top tier. Bedroom counts come in via `bdrmcnt_N`. Mix tier and bedroom in URLs — don't hand-edit, lift from the variant list.
- **ZHVF is a growth forecast, not a level.** ZHVF columns are MoM%, QoQ%, YoY% — apply to current ZHVI to project. Do not chart ZHVF as a price level.
- **Nowcast cuts revise.** Sales count, median sale price, mean sale price, and total transaction value publish "nowcast" variants that get revised as off-market data lands. Pull the latest CSV every time; don't cache the trailing month's number.
- **No published rate limit, but be polite.** Zillow doesn't enforce per-IP throttling on the public CSVs, but they're hosted on a static CDN. Cache locally; refresh monthly aligns with the publishing cadence.
- **Forecast is national-only for rent.** ZORF (rent forecast) ships at national grain. For metro rent calls, pair ZORI's trailing trend with your own top-down — Zillow doesn't publish a metro-level ZORF.

## Source of truth

This skill is derived from TiRE's canonical catalog at [agents/data/zillow-datasets.yaml](https://github.com/analyticsariel/tech-in-real-estate-ops/blob/main/agents/data/zillow-datasets.yaml). The YAML is hand-curated; every entry has a `why_it_matters` rationale that feeds both this skill and TiRE's research agents.

When the upstream catalog changes, regenerate `references/metrics.md` and `references/zillow-datasets.yaml`. v1 is hand-curated; build script deferred until drift is observed.
