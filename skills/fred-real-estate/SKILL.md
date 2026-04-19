---
name: fred-real-estate
description: Reference US housing-market macro indicators from FRED (Federal Reserve Economic Data) for real estate investment decisions. Use this skill whenever a user asks about mortgage rates, home prices, Case-Shiller, FHFA HPI, housing starts, building permits, months supply, days on market, home sales, CPI rent, owners' equivalent rent, rental vacancy, homeownership rate, unemployment, nonfarm payrolls, real disposable income, CPI, PCE, mortgage delinquency, charge-off rates, household debt service, Fed funds, Treasury yields, prime rate, yield curve, housing affordability, US housing macro, Federal Reserve data, BLS housing data, NAR data, or which economic series inform a residential RE decision. Maps 44 FRED series across 9 categories (rates_financing, prices, affordability, supply, demand, rental_market, macro_labor, inflation, credit_stress) to investor use-cases. Progressive disclosure — decision playbooks and the full 44-series reference live in `references/`.
---

# FRED for Real Estate

## What is FRED

FRED is the Federal Reserve Bank of St. Louis's public data portal — [fred.stlouisfed.org](https://fred.stlouisfed.org). Free, no signup to browse, ~800,000 economic time series from the Fed, BLS, Census, Treasury, NAR, S&P, Freddie Mac, and others. For US residential real estate, it's the authoritative single stop for mortgage rates, home-price indices, affordability, employment, rent inflation, and credit conditions.

FRED is national and metro-level only. For local/ZIP pricing, use Zillow, Redfin, Realtor.com, or Census ACS — not FRED.

## Bundled resources

| File | When to load |
|---|---|
| `references/metrics.md` | When a user asks about a specific metric, needs a `series_id` to pull, or any decision playbook below points here. Full 44-series list, grouped by category, with one-line rationale each. |
| `references/fred-series.yaml` | When you need richer metadata than `metrics.md` provides — tags, source publisher, FRED landing-page URL, data-quality notes. The canonical catalog, 100% field coverage. |

Progressive disclosure rule: start with this file and the category table below. Read `references/metrics.md` only when a specific metric or `series_id` is actually needed. Read the YAML only when the markdown is insufficient.

## Getting an API key

1. Create a free account at [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html). Instant.
2. Set environment variable: `FRED_API_KEY=your_key_here`
3. Install the Python client: `pip install fredapi`
4. Rate limit is 120 req/min — not a concern for individual use.

## Minimal Python example

```python
import os
from fredapi import Fred

fred = Fred(api_key=os.environ["FRED_API_KEY"])

rates = fred.get_series("MORTGAGE30US")
print(rates.tail())
```

Swap `MORTGAGE30US` for any `series_id` from `references/metrics.md`.

## The 9 categories

| Category | Purpose | Count |
|---|---|---|
| `rates_financing` | Cost of money: mortgage, Treasury, Fed, prime | 7 |
| `prices` | What homes cost: medians and price indices | 7 |
| `affordability` | Rates + prices + income, fused | 1 |
| `supply` | Pipeline and inventory: permits → starts → completions → active listings | 7 |
| `demand` | Transaction volume and velocity | 4 |
| `rental_market` | Rent inflation, vacancy, tenure | 5 |
| `macro_labor` | Jobs and incomes — who pays the rent | 5 |
| `inflation` | CPI, PCE, and the Fed's target | 4 |
| `credit_stress` | Delinquency, charge-offs, debt service | 4 |

Total: 44 series. See `references/metrics.md` for the full list with `series_id`s.

## Decision playbooks

Concrete "the user asked X — here's the series-id set to pull." Use these as starting points; extend when the question demands it. If a playbook names a series, `references/metrics.md` has the one-line rationale.

**"Is now a good time to buy?"**
→ `MORTGAGE30US`, `FIXHAI`, `CSUSHPINSA`, `MSACSR`, `MEDDAYONMARUS`
Cost of capital, affordability index, price trajectory, supply balance, velocity. Affordability + supply together tell you leverage.

**"Is a downturn coming?"**
→ `UNRATE`, `DGS10` vs `DGS2` (yield curve), `DRSFRMACBS`, `TDSP`, `PAYEMS`
Labor cracks first, curve inverts early, mortgage delinquencies are the coincident tell, debt-service ratio shows fragility.

**"How's the rental market?"**
→ `CUSR0000SEHA`, `RRVRUSQ156N`, `RHORUSQ156N`, `DSPIC96`
Rent inflation, vacancy (pricing power), homeownership rate (tenure shift), income (can tenants absorb raises).

**"Cost of capital moving?"**
→ `DGS10`, `MORTGAGE30US`, `FEDFUNDS`, `DPRIME`
10Y leads 30Y mortgage. Fed funds sets the floor. Prime for HELOCs.

**"Supply: tight or loose?"**
→ `PERMIT`, `HOUST`, `COMPUTSA`, `MSACSR`, `ACTLISCOUUS`
Permits (6–12mo out) → starts (3–6mo) → completions (now). Months-supply is the balance read.

**"Is rent inflation cooling?"**
→ `CUSR0000SEHA`, `CUSR0000SEHC01`, `PCEPILFE`
CPI rent is reported; OER is the Fed's imputed measure and the biggest shelter driver of Core PCE.

## Gotchas

- **Seasonal adjustment matters.** Supply and demand series are usually SA (seasonally adjusted). Rates and home prices are often NSA. Don't compare SA to NSA without normalizing.
- **SAAR = seasonally adjusted annual rate.** A monthly reading of "1,500" housing starts means 1.5M on an annualized basis, not 1,500 in that month.
- **Release lag is real.** Case-Shiller ~2 months, FHFA quarterly, real median HH income ~9 months. Don't report stale data as current.
- **`FIXHAI` only retains 13 months on FRED** per NAR's agreement. For longer series, pull from NAR directly.
- **FRED is national/metro only.** Don't use these series for ZIP or neighborhood decisions. Pair with Zillow/Redfin/Census.
- **Two versions of Fed funds.** `DFF` is daily, `FEDFUNDS` is monthly. Use daily for news-driven analysis, monthly for charts.

## Source of truth

This skill is derived from TiRE's canonical catalog at [agents/data/fred-series.yaml](https://github.com/analyticsariel/tech-in-real-estate-ops/blob/main/agents/data/fred-series.yaml). The YAML is hand-curated; every entry has a `why_it_matters` rationale that feeds both this skill and TiRE's research agents.

When the upstream catalog changes, regenerate `references/metrics.md` and `references/fred-series.yaml`. v1 is hand-curated; build script deferred until drift is observed.
