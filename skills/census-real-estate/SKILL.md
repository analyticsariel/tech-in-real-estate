---
name: census-real-estate
description: Reference US demographics, household income, and housing-stock data from Census (U.S. Census Bureau, American Community Survey 5-Year Estimates) for real estate investment decisions. Use this skill whenever a user asks about ACS, ACS 5-Year, Census tract data, block-group demographics, median household income, median home value, median gross rent, median owner costs, rent burden, homeownership rate, vacancy rate, housing units, year built, population growth, educational attainment, bachelor's-degree share, labor force participation, B25 housing tables, B19013, B25064, B25077, county-grain demand benchmarks, or which Census variables underwrite a residential RE decision. Maps 12 ACS 5-Year metrics across 5 categories (demographics, income_affordability, housing_costs, tenure_vacancy, housing_stock) to investor use-cases. Progressive disclosure — decision playbooks and the full 12-dataset reference live in `references/`.
---

# Census for Real Estate

## What is Census

Census is the U.S. Census Bureau's public data portal — [data.census.gov](https://data.census.gov). Free, API-keyed, and the only free source that publishes household-level demographics, income, and housing-stock data down to block-group grain. For US residential real estate, it's the authoritative single stop for tract-level demand reads — population, income, education, tenure, rent burden, and housing stock — that no listing feed or macro source covers.

This skill targets the **American Community Survey (ACS) 5-Year Estimates** specifically. Each vintage is a 5-year pooled estimate released annually each December; the 5-Year (not 1-Year) flavor is the only one that fills at every geography investors cite — counties under 65k population and every tract simply don't appear in 1-Year. For current-cycle pricing and listings, pair Census with Redfin, Realtor, or Zillow — Census is slower than the listing feeds but goes finer than any of them.

## Bundled resources

| File | When to load |
|---|---|
| `references/metrics.md` | When a user asks about a specific dataset, needs a `dataset_key` or ACS variable ID to pull, or any decision playbook below points here. Full 12-dataset list, grouped by category, with verbatim rationale each. |
| `references/census-datasets.yaml` | When you need richer metadata than `metrics.md` provides — ACS table IDs, variable names, derivation blocks, benchmark geographies, notes. The canonical catalog, 100% field coverage. |

Progressive disclosure rule: start with this file and the category table below. Read `references/metrics.md` only when a specific dataset or `dataset_key` is actually needed. Read the YAML only when the markdown is insufficient.

## Getting an API key

1. Request a free key at [api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html). Arrives by email in minutes.
2. Set environment variable: `CENSUS_API_KEY=your_key_here`
3. No dedicated client needed — `requests` and `pandas` cover every pull. A `pip install census` wrapper exists if you want one.
4. Rate limit: 500 requests/day per IP without a key, effectively unlimited with one. Get the key.

## Minimal Python example

```python
import os
import requests

CENSUS_API_KEY = os.environ["CENSUS_API_KEY"]

# Median household income — Hillsborough County, FL — ACS 5-Year 2024
url = (
    "https://api.census.gov/data/2024/acs/acs5"
    "?get=NAME,B19013_001E&for=county:057&in=state:12"
    f"&key={CENSUS_API_KEY}"
)
header, row = requests.get(url, timeout=30).json()
print(row[0], int(row[1]))
```

Swap `B19013_001E` for any ACS variable from `references/metrics.md`.

## The 5 categories

| Category | Purpose | Count |
|---|---|---|
| `demographics` | Who lives here: population, education, labor-force engagement | 3 |
| `income_affordability` | What households earn and how much rent that can carry | 2 |
| `housing_costs` | Rent, owner costs, home value — both sides of the rent-vs-buy line | 3 |
| `tenure_vacancy` | Owner vs renter, occupied vs vacant — market-structure reads | 2 |
| `housing_stock` | Scale and age of the local housing stock | 2 |

Total: 12 datasets. See `references/metrics.md` for the full list with `dataset_key`s and ACS variable IDs.

## Decision playbooks

Concrete "the user asked X — here's the dataset-key set to pull." Use these as starting points; extend when the question demands it. If a playbook names a dataset, `references/metrics.md` has the verbatim rationale.

**"Can renters here afford a $2,000/mo unit?"**
→ `census_median_income`, `census_median_gross_rent`, `census_median_rent_burden`
Apply the 30%-of-income rule to median income for the local rent ceiling, then read gross rent and the rent-burden median to see how much room is left.

**"Is this market rent-vs-buy biased?"**
→ `census_median_gross_rent`, `census_median_owner_costs`, `census_median_home_value`, `census_homeownership_rate`
Symmetric pair: rent vs all-in mortgaged carry. Add home value and the owner share to read whether the market structurally favors one tenure.

**"What does the demand side look like?"**
→ `census_population`, `census_bachelors_or_higher`, `census_labor_force_participation`
Population growth is the demand denominator; bachelor's-share momentum signals high-income inflow; LFPR says how many adults can actually pay rent.

**"Is this market tight or loose?"**
→ `census_vacancy_rate`, `census_homeownership_rate`, `census_housing_units`
Vacancy under ~7% = tight (rents push, leasing compresses); above ~12% = loose. Tenure mix and stock scale add context.

**"Is the housing stock aging or expanding?"**
→ `census_housing_units`, `census_median_year_built`
YoY housing-units growth is net new construction. Median year built drifting older = construction lagging growth, value-add opportunity widens.

**"Is this market priced to local income or imported demand?"**
→ `census_median_income`, `census_median_home_value`, `census_median_gross_rent`
Benchmark the county to FL + US on each. Income-aligned pricing = local-market; price and rent decoupled from income = exogenous demand (in-migration, vacation, institutional capital).

## Gotchas

- **5-Year ≠ a single year.** ACS 5-Year vintages are pooled 5-year averages. The 2024 vintage covers 2020–2024, not just 2024. Don't compare a 5-Year reading to a 1-Year or single-year point estimate without normalizing the window.
- **Annual release lag.** New ACS 5-Year vintages drop every December. Through Q3, the most recent vintage is ~9–21 months stale relative to the current cycle.
- **1-Year doesn't exist for most counties.** Anything under 65k population and every census tract only ships in the 5-Year flavor. For a freshest single-year estimate at sub-metro grain, you can't get it from Census — go to listing-feed sources.
- **Self-reported home values.** B25077 is the owner's estimate of market value, not a transaction price. Lags the real cycle by the 5-year pooling window; cross-check Realtor / Zillow / Redfin for current-cycle marks.
- **Inflation-adjusted to vintage end-year.** B19013 dollars are real-to-the-vintage. Year-over-year comparisons across vintages are nominal — adjust separately for real growth.
- **Margin of error widens at smaller geographies.** County is the safe default. Tract and block-group MOEs can run ~20% of the estimate; don't push a single-tract reading without checking the published MOE.
- **Gross rent (B25064) ≠ contract rent (B25031).** Gross includes utilities, contract doesn't. Most investor comps quote gross — match what your comps use.
- **Derived metrics need the derivation.** Homeownership rate, vacancy rate, bachelor's-share, and LFPR are computed from raw variables. The catalog's `derivation` block specifies the formula — don't pull a single variable and expect a percentage.

## Source of truth

This skill is derived from TiRE's canonical catalog at [agents/data/census-datasets.yaml](https://github.com/analyticsariel/tech-in-real-estate-ops/blob/main/agents/data/census-datasets.yaml). The YAML is hand-curated; every entry has a `why_it_matters` rationale that feeds both this skill and TiRE's research agents.

When the upstream catalog changes, regenerate `references/metrics.md` and `references/census-datasets.yaml`. v1 is hand-curated; build script deferred until drift is observed.
