---
name: hmda-real-estate
description: Reference mortgage origination, denial, refi, product-mix, loan-size, property-type, and fair-lending data from HMDA (Home Mortgage Disclosure Act, CFPB Data Browser aggregations) for real estate investment decisions. Use this skill whenever a user asks about HMDA data, Home Mortgage Disclosure Act, CFPB data, mortgage originations, mortgage applications, denial rate, denial rates, refi count, cash-out refi share, purchase share, FHA share, VA share, conventional share, loan volume, average loan amount, small-multi share, 2-to-4 unit financing, manufactured home loans, fair lending, Black applicant denial rate, credit access, mortgage underwriting, tightening standards, Hillsborough County, Tampa mortgage market, county-grain credit, or which HMDA fields inform a residential RE decision against Florida and US benchmarks. Maps 14 HMDA aggregation metrics across 6 categories (credit_access, loan_purpose_cycle, product_mix, volume_size, property_type, fair_lending) to investor use-cases. Progressive disclosure — decision playbooks and the full 14-metric reference live in `references/`.
---

# HMDA for Real Estate

## What is HMDA

HMDA is the Home Mortgage Disclosure Act reporting regime the CFPB runs — [ffiec.cfpb.gov/data-browser](https://ffiec.cfpb.gov/data-browser). Free, no signup, a JSON aggregations API plus the raw Loan/Application Record (LAR) download. Every US mortgage lender above a volume threshold files annually; the Data Browser aggregates those filings into {count, sum} buckets per geography and year. For US residential real estate, it's the authoritative single stop for who actually got financed, who got turned away, what product they used, and how much money moved — at national, state, MSA, or county grain.

HMDA's aggregations endpoint ships at county grain (`counties=12057`) and fills reliably for every metric in this catalog. For weekly listing velocity or sale-side pricing, pair with Redfin or Realtor. For tract-level demographic context behind the credit story, pair with Census ACS. For the rate regime HMDA lenders quote against, pair with FRED's `MORTGAGE30US`.

## Bundled resources

| File | When to load |
|---|---|
| `references/metrics.md` | When a user asks about a specific HMDA metric, needs an `api_endpoint` to hit, or any decision playbook below points here. Full 14-metric list, grouped by category, with verbatim rationale each. |
| `references/hmda-datasets.yaml` | When you need richer metadata than `metrics.md` provides — full API URLs, benchmark geographies, copy-pasteable Python snippets, fetcher notes. The canonical catalog, 100% field coverage. |

Progressive disclosure rule: start with this file and the category table below. Read `references/metrics.md` only when a specific metric or `api_endpoint` is actually needed. Read the YAML only when the markdown is insufficient.

## Getting an API key

1. No API key required. The CFPB Data Browser aggregations endpoint is public JSON — hit it with `requests.get` directly.
2. No environment variable to set. The catalog's `api_endpoint` fields are URL templates with a `{year}` placeholder; substitute the year and GET.
3. No dedicated client. `pip install requests` covers every pull.
4. No published rate limit. Scoping hit zero 429s across ~40 test calls; `servedFrom=cache` on repeats confirms server-side caching. A full 14-metric × 7-year × 3-geo refresh is ~420 GETs — well inside polite-client territory.

## Minimal Python example

```python
import requests

# HMDA originations — Hillsborough County, FL, 2024
YEAR = 2024
url = (
    "https://ffiec.cfpb.gov/v2/data-browser-api/view/aggregations"
    f"?years={YEAR}&counties=12057&actions_taken=1"
)
response = requests.get(url, timeout=30)
response.raise_for_status()
originations = response.json()["aggregations"][0]["count"]
print(f"{YEAR} Hillsborough County originations: {originations:,}")
```

Swap `counties=12057` for `states=FL` (Florida benchmark) or the 51-state comma-joined list (national rollup — see gotchas). Swap `actions_taken=1` and add the filter set from any `api_endpoint` in `references/metrics.md` to pull a different metric.

## The 6 categories

| Category | Purpose | Count |
|---|---|---|
| `credit_access` | Is credit flowing: originations, applications, denial rate | 3 |
| `loan_purpose_cycle` | What borrowers are doing: purchase vs refi, cash-out mix | 3 |
| `product_mix` | How borrowers finance: FHA, VA, conventional shares | 3 |
| `volume_size` | How much money moves: total $ volume, avg purchase loan | 2 |
| `property_type` | What's being financed: small-multi (2–4 unit), manufactured | 2 |
| `fair_lending` | Equity-of-access read: Black applicant denial rate | 1 |

Total: 14 metrics. See `references/metrics.md` for the full list with `api_endpoint`s.

## Decision playbooks

Concrete "the user asked X — here's the metric set to pull." Use these as starting points; extend when the question demands it. If a playbook names a metric, `references/metrics.md` has the verbatim rationale.

**"Is credit loosening or tightening in Hillsborough?"**
→ `hmda_originations_count`, `hmda_application_count`, `hmda_denial_rate`
Applications lead originations by a quarter; denial rate is the underwriting posture. Run all three against FL + US to see whether Tampa's credit stance is moving with the cycle or against it.

**"Where is the mortgage cycle right now?"**
→ `hmda_purchase_share`, `hmda_refi_count`, `hmda_cashout_refi_share`
When rates drop, refi takes over and purchase share craters; when rates climb, purchase is most of what's left. Cash-out share above rate-term refi is a late-cycle equity-extraction read.

**"Who's financing marginal buyers here?"**
→ `hmda_fha_share`, `hmda_va_share`, `hmda_conventional_share`
FHA is the 3.5%-down entry-level product; VA is military-only; conventional is the prime-credit baseline. Shares shifting toward FHA is an affordability-stress signal; conventional receding means the borrower base is weakening.

**"How much capital is actually moving through Hillsborough?"**
→ `hmda_loan_volume`, `hmda_avg_purchase_loan_amount`, `hmda_originations_count`
Volume = count × avg size. When volume moves but count doesn't, loan sizes are shifting (affordability or migration pressure). Mean vs median gap isn't available without raw LAR, so use mean with care.

**"What's the non-single-family financing story?"**
→ `hmda_small_multi_share`, `hmda_manufactured_share`
2-to-4-unit is the house-hacker bucket TiRE's audience operates in; manufactured is the cheap-entry affordability read. Both run below 2% in most counties — interpret slopes, not absolute levels.

**"Is credit access equitable here?"**
→ `hmda_black_applicant_denial_rate`, `hmda_denial_rate`
One fair-lending metric against the overall denial rate, benchmarked to FL + US. Question the data can answer: is Hillsborough converging with or diverging from the state and national patterns for this applicant group?

## Gotchas

- **Aggregations require a geo filter — there is no no-geo mode.** Passing the endpoint without `counties`, `states`, `msamds`, or `leis` returns `{"errorType":"provide-only-msamds-or-states-or-counties-or-leis"}`. National rollup = all 51 jurisdictions in a single `states=AL,AK,AZ,...` list, which collapses to one aggregation row that is the true US total. The fetcher in `agents/sources/hmda.py` carries the 51-state constant; if you're rolling your own, do the same (decision #94).
- **Max 2 non-geo filter criteria.** More returns `{"errorType":"provide-two-or-less-filter-criteria"}`. Filter budget shapes the catalog: `hmda_fha_share` / `hmda_va_share` / `hmda_conventional_share` are "as % of all originations" (2 criteria: `actions_taken` + `loan_types`), not "as % of purchase originations" (would be 3). Purchase-cycle signal lives in `hmda_purchase_share`; product mix is blended-purpose by necessity (decision #94).
- **Six filters silently no-op.** `occupancy_types`, `hoepa_statuses`, `open_end_line_of_credits`, `preapprovals`, `business_or_commercial_purposes`, `ages` — exposed in HMDA's raw LAR but not implemented on aggregations. Pass them and you get the same response as not passing them. Investor-property share, HELOC share, HOEPA flag, preapproval funnel, business-purpose share, and age-bracket splits are therefore out of scope here (decision #93).
- **State `code` is two-letter abbreviation, not FIPS.** `states=FL`, not `states=12`. Catalog's `benchmark_geos[]` state entry carries `code: "FL"` for exactly this reason while `geo_key` stays FIPS-based (`state_12`) for cross-source joins (decision #90).
- **Annual cadence, summer-of-next-year lag.** The 2024 LAR loaded in the Data Browser on 2026-04-19. 2025 LAR lands summer 2026. `YEAR_SPAN` in `agents/sources/hmda.py` is `(2018, 2024)` — 7 annual observations — bump manually when 2025 loads (decision #91).
- **No median field on aggregations.** The response ships `{count, sum}` per bucket. Median loan amount, rate spread, LTV distributions all require raw LAR (~2B rows across all years — different data-engineering surface per decision #53). `hmda_avg_purchase_loan_amount` is mean-not-median on purpose.
- **`servedFrom` tells you cached vs live.** Response carries `"servedFrom": "cache" | "db"`. On the first GET per (filter, year) pair you get `db`; repeats get `cache`. Useful for debugging unexpected latency, and the catalog's batch fetcher relies on it amortizing repeat hits.
- **Geo grain swap landed in Sprint 14.** Earlier sprints pulled at Tampa MSA (`msamds=45300`); current catalog is Hillsborough County (`counties=12057`) for cross-source comparability with Census / Realtor / Redfin / Zillow. If you need MSA, the URL still works — just not in the catalog (decision #89).

## Source of truth

This skill is derived from TiRE's canonical catalog at [agents/data/hmda-datasets.yaml](https://github.com/analyticsariel/tech-in-real-estate-ops/blob/main/agents/data/hmda-datasets.yaml). The YAML is hand-curated; every entry has a `why_it_matters` rationale that feeds both this skill and TiRE's research agents.

When the upstream catalog changes, regenerate `references/metrics.md` and `references/hmda-datasets.yaml`. v1 is hand-curated; build script deferred until drift is observed.
