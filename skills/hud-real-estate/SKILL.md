---
name: hud-real-estate
description: Reference rent ceilings, income limits, and cost-burden tabulations from HUD (U.S. Department of Housing and Urban Development, HUD USER API) for real estate investment decisions. Use this skill whenever a user asks about HUD data, Fair Market Rent, FMR, Section 8 voucher ceiling, payment standard, Area Median Income, AMI, HAMFI, income limits, 30% AMI, 50% AMI, 80% AMI, LIHTC rent caps, MTSP income limits, 60% AMI set-aside, CHAS, Consolidated Housing Affordability Strategy, renter cost burden, severe cost burden, owner cost burden, housing problems, extremely low income renters, priority tenant pool, Hillsborough County, Tampa voucher rent, voucher underwriting, affordable housing eligibility, or which HUD endpoints inform a residential RE decision against Florida and US benchmarks. Maps 12 HUD metrics across 3 categories (rent_ceilings, income_limits, housing_needs) to investor use-cases. Progressive disclosure — decision playbooks and the full 12-metric reference live in `references/`.
---

# HUD for Real Estate

## What is HUD USER

HUD USER is HUD's public data portal — [huduser.gov](https://www.huduser.gov/) — and its Bearer-token API exposes the four datasets this skill covers: Fair Market Rent (FMR), Income Limits (IL), Multifamily Tax Subsidy Program Income Limits (MTSP IL), and the Comprehensive Housing Affordability Strategy custom-ACS tabulations (CHAS). Four endpoints, one token, three programs that shape every voucher and LIHTC deal in the country.

For a tech RE investor: HUD is the **policy layer** that sits on top of Census demographics and market rent data. Census tells you the demand pool; Redfin/Zillow tell you where the market is pricing; HUD tells you the literal ceiling a Section 8 voucher will pay, the income line that defines "low-income" for every affordable-housing program, the rent cap on LIHTC set-asides, and the share of the county's renters paying more than half their income to a landlord.

This skill anchors on **Hillsborough County, FL** — HUD entityid `1205799999` for FMR/IL/MTSP IL, CHAS parameters `type=3&stateId=12&entityId=57`. Benchmarks bifurcate by endpoint (decision #93): FMR ships no benchmarks (HUD doesn't publish state/national aggregates — FMR is MSA-assigned by statute), IL ships Florida only (no national AMI endpoint exists), CHAS ships Florida + US (native via `type=1` nation + `type=2` state). The chart reading honestly reflects what HUD actually publishes.

## Bundled resources

| File | When to load |
|---|---|
| `references/metrics.md` | When a user asks about a specific metric, needs an extractor or variable code, or any decision playbook below points here. Full 12-metric list grouped by category, with extractor path + verbatim rationale each. |
| `references/hud-datasets.yaml` | When you need richer metadata than `metrics.md` provides — API endpoints, full Python snippets, benchmark configs, CHAS derivation blocks, fetcher notes. The canonical catalog, 100% field coverage. |

Progressive disclosure rule: start with this file and the category table below. Read `references/metrics.md` only when a specific metric is actually needed. Read the YAML only when the markdown is insufficient (usually: pulling CHAS derivations or verifying the exact entityid / API parameters).

## Getting an API key

1. Sign in at [huduser.gov](https://www.huduser.gov/). Click your username → **User Profile** → **Access Token**.
2. Generate a token (JWT, ~500 chars). Copy it.
3. Set `HUD_API_KEY` in your environment. Same key works across all four endpoints (FMR, IL, MTSP IL, CHAS).
4. HUD's documented rate limit is ~100 req/min; observed burst protection on `/chas` specifically kicks in harder. A 2-second inter-request sleep keeps you under the wire across all four endpoints.

## Minimal Python example

```python
import os
import requests

HUD_API_KEY = os.environ["HUD_API_KEY"]
ENTITY_ID = "1205799999"  # Hillsborough County, FL (HUD county format: {state_fips}{county_fips}99999)
headers = {"Authorization": f"Bearer {HUD_API_KEY}"}

# FMR — 2-bedroom voucher ceiling
url = f"https://www.huduser.gov/hudapi/public/fmr/data/{ENTITY_ID}?year=2026"
r = requests.get(url, headers=headers, timeout=30)
r.raise_for_status()
msa_row = next(row for row in r.json()["data"]["basicdata"] if row["zip_code"] == "MSA level")
print("2BR FMR FY2026:", msa_row["Two-Bedroom"])

# CHAS — renter severe cost burden rate (needs float cast; CHAS returns counts as strings)
url = "https://www.huduser.gov/hudapi/public/chas?type=3&stateId=12&entityId=57&year=2018-2022"
row = requests.get(url, headers=headers, timeout=30).json()[0]
rate = float(row["D8"]) / float(row["A17"]) * 100
print(f"Renter severe cost burden: {rate:.1f}%")
```

Swap the endpoint and extractor for any metric in `references/metrics.md`. The 12 featured entries split across 4 HUD endpoints — one token, four response shapes.

## The 3 categories

| Category | Purpose | Count | Endpoint(s) |
|---|---|---|---|
| `rent_ceilings` | Fair Market Rent — what a Section 8 voucher legally pays | 2 | `/fmr/data` |
| `income_limits` | AMI thresholds for Section 8, LIHTC, and affordable-housing eligibility | 5 | `/il/data` (4) + `/mtspil/data` (1) |
| `housing_needs` | Cost burden × tenure and priority-tenant-pool counts from ACS custom tabs | 5 | `/chas` |

Total: 12 metrics. See `references/metrics.md` for the full list with extractors.

## Decision playbooks

### 1. "What's the max a voucher pays on a 3BR in Tampa?"

Pull **`hud_fmr_3br`** (`/fmr/data/1205799999?year=2026`, extract `row["Three-Bedroom"]` where `zip_code == "MSA level"`). That number is the voucher rent ceiling for a 3-bedroom unit under Section 8 in the Tampa MSA. HUD publishes a fresh FMR schedule every fiscal year (released in October); the current FY is labeled by its ending year.

If your pro forma includes voucher tenants at an asking rent above this number, the deal doesn't work with Section 8 — a voucher won't cover the gap. If your asking rent is below FMR, you've got room to raise toward the ceiling without losing voucher eligibility.

For a 2BR cut (the more common voucher placement), swap to **`hud_fmr_2br`**.

### 2. "Does this tenant actually qualify for the Section 8 unit I'm marketing?"

Pull **`hud_il_50ami_4person`** (`/il/data/1205799999?year=2025`, extract `data["very_low"]["il50_p4"]`). That's the 50% AMI income limit for a 4-person household in Hillsborough — the default Section 8 voucher eligibility line. Household income under this number = eligible for a voucher; household income above it = not eligible.

For smaller/larger households, substitute `il50_p1` through `il50_p8` for household sizes 1-8 (same response, different key). For the 30% AMI extremely-low priority tier, pull **`hud_il_30ami_4person`** instead.

### 3. "What's the rent cap on a LIHTC 60% AMI set-aside unit?"

Pull **`hud_mtspil_60ami_4person`** (`/mtspil/data/1205799999?year=2025`, extract `data["60percent"]["il60_p4"]`). The LIHTC rent cap is **30% of this income number, minus a utility allowance** — a dollar ceiling on monthly rent for that unit class. This is the MTSP IL endpoint (different from standard IL), and it's the anchor behind the most common FL LIHTC deal type.

There's no state benchmark for MTSP IL — `/mtspil/statedata/FL` returns 404; HUD doesn't publish state rollups for MTSP tiers.

### 4. "How stretched is the Hillsborough renter pool right now?"

Pull **`hud_chas_renter_severe_cost_burden`** (`/chas?type=3&stateId=12&entityId=57&year=2018-2022`, derivation `D8 / A17 × 100`). That's the share of renter households paying more than 50% of income to housing — HUD's federal definition of severe cost burden. Benchmark against **FL** (`type=2&stateId=12`) and **US** (`type=1`) to see whether Hillsborough renters are more or less stretched than the baseline.

Above ~25% = wide renter pool under real strain, which caps how hard you can push on rent and raises your delinquency forecast. Read together with **`hud_chas_renter_severe_housing_problems`** (`C2 / A17 × 100`) — that's a broader distress signal including unit-quality issues (missing kitchens, bad plumbing, severe overcrowding) *on top of* severe cost burden.

### 5. "How big is the addressable pool for my voucher / LIHTC / workforce-housing strategy?"

Pull **`hud_chas_renter_households_below_80ami`** (derivation `A2 + A5 + A8` from the same CHAS response). That's the count of renter households at or below 80% HAMFI in Hillsborough — the demand pool every affordable-housing program competes for. Benchmark against Florida and the US to see whether the local eligible-renter base is proportionally larger or smaller than the baseline.

For the deep-affordable slice specifically (Section 8 priority, LIHTC 30% basis boost), pull **`hud_chas_extremely_low_income_renters`** (`A2` alone) — renter households at ≤30% AMI, the priority-tenant pool.

### 6. "Is Florida's insurance + HOA crisis showing up in owner financials?"

Pull **`hud_chas_owner_cost_burden`** (derivation `(D4 + D7) / A16 × 100`). That's the share of *owner* households (both mortgaged and free-and-clear) paying over 30% of income to housing. In Florida this number moves with insurance premiums and HOA assessments, not just mortgage rates — a meaningful jump between CHAS vintages usually signals a carrying-cost shock.

If owner cost burden is climbing while your acquisition thesis assumes "owners are comfortable," that's a reprice-risk signal for the for-sale market.

## Gotchas

1. **HUD's county entityid routes to the parent MSA for FMR.** Querying `/fmr/data/1205799999` returns the Tampa MSA FMR schedule — the county number is the MSA number because HUD assigns FMR at Fair Market Area grain. For the per-ZIP SAFMR cuts underneath (Tampa is SAFMR-designated as of FY26), read the rest of `data.basicdata` rows beyond the `"MSA level"` sentinel.
2. **CHAS API coding is NOT the CSV-download coding.** HUD's CHAS data-dictionary spreadsheet uses `T{n}_est{m}` variable codes. The CHAS API uses `A1`-`J17` codes — 132 variables across 10 groups (A-J). The two systems don't map 1:1. Use the API coding when pulling from `/chas` (the catalog's `derivation` blocks already do).
3. **CHAS returns numeric counts as strings.** `row["D8"]` comes back as `"55390.0"`, not `55390.0`. Cast with `float()` before arithmetic or you'll get a `TypeError`.
4. **MTSP IL has no statedata endpoint.** `/mtspil/statedata/FL` returns 404. There's no state-level MTSP aggregate, so MTSP IL metrics ship single-line with no benchmark.
5. **No national AMI exists.** HUD publishes AMI at metro/county grain and state grain (via `/il/statedata`) — but not nationally. The "area" in Area Median Income is definitionally local; `/il/nationaldata`, `/il/data/US`, and `/il/statedata/US` all 400. This is why IL metrics in the catalog carry a Florida benchmark but no US benchmark.
6. **USPS Vacancy is NOT publicly accessible.** HUD publishes quarterly USPS vacancy aggregates — but they're restricted to government + non-profit users via a signed sublicense. Readers can't register. The catalog doesn't include it for exactly this reason.
7. **CHAS releases on a ~3-year lag.** A CHAS vintage covers a 5-year ACS window (e.g. `2018-2022`) and is published roughly 3 years after the end of the window. The latest CHAS available is `2018-2022` (released Dec 2025); next release will be `2019-2023`. Don't expect current-year cost burden.

## Credits & provenance

- Source catalog: [`agents/data/hud-datasets.yaml`](../../agents/data/hud-datasets.yaml) in the private ops repo.
- Shipped in Sprint 13 (HUD deepen: 12 metrics × Hillsborough × bifurcated benchmarks). Decisions #89-#94.
- The 12 `why_it_matters` blocks in `references/metrics.md` are lifted verbatim from the canonical catalog's TiRE-voice prose. Not generated — hand-edited to investor lens.
- This skill was authored via the [`tire-source-skill-builder`](../tire-source-skill-builder/) meta-skill following the Census/Realtor/Redfin/Zillow same-day-ship pattern (decisions #87/#88).
