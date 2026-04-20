---
name: fema-real-estate
description: Reference disaster declarations, NFIP flood insurance claims, Individual Assistance grants to households, and Public Assistance federal obligations from FEMA (Federal Emergency Management Agency, OpenFEMA v2) for real estate investment decisions. Use this skill whenever a user asks about FEMA data, OpenFEMA, disaster declarations, federally declared disasters, hurricane declarations, NFIP, National Flood Insurance Program, flood claims, flood insurance, NFIP payouts, NFIP claim severity, building damage assessed, IHP, Individuals and Households Program, disaster assistance, IHP grants, owner IA, renter IA, disaster registrations, Public Assistance, PA federal obligation, permanent work share, debris removal, emergency protective measures, damage category, Hillsborough County, Tampa flood risk, Tampa hurricane exposure, county-grain climate risk, or which FEMA datasets inform a residential RE decision against Florida and US benchmarks. Maps 12 FEMA metrics across 4 categories (disaster_frequency, flood_insurance, individual_assistance, public_assistance) to investor use-cases. Progressive disclosure — decision playbooks and the full 12-metric reference live in `references/`.
---

# FEMA for Real Estate

## What is FEMA / OpenFEMA

FEMA is the Federal Emergency Management Agency; OpenFEMA v2 is its public data API — [fema.gov/about/openfema](https://www.fema.gov/about/openfema). Free, no signup, no API key, OData-style `$filter` + `$top` + `$skip` on every dataset. Event-row data: one row per disaster × county designation, one row per NFIP claim, one row per PA-funded project, etc. For US residential real estate this is the authoritative free read on the climate + insurance exposure layer — how often disasters hit a county, what the flood-insurance market actually settled, how much federal money flowed to households and infrastructure.

FEMA lands at county grain cleanly (with per-dataset encoding quirks, see Gotchas). For the rent cap / income limit / AMI side of the housing-policy story, pair with HUD. For the ZIP-level home-value context around flood exposure, pair with Zillow. For local-area labor employment that tracks displacement recovery, pair with BLS.

## Bundled resources

| File | When to load |
|---|---|
| `references/metrics.md` | When a user asks about a specific FEMA metric, needs an `api_endpoint` to hit, or any decision playbook below points here. Full 12-metric list, grouped by category, with verbatim rationale each. |
| `references/fema-datasets.yaml` | When you need richer metadata than `metrics.md` provides — full API URLs, benchmark geographies, copy-pasteable Python snippets, fetcher notes on per-dataset county encoding. The canonical catalog, 100% field coverage. |

Progressive disclosure rule: start with this file and the category table below. Read `references/metrics.md` only when a specific metric or `api_endpoint` is actually needed. Read the YAML only when the markdown is insufficient.

## Getting an API key

1. No API key required. OpenFEMA v2 is public JSON — hit it with `requests.get` directly.
2. No environment variable to set. The catalog's `api_endpoint` fields are URL templates with a `{code}` placeholder; substitute the geo code (format varies per dataset, see Gotchas) and GET.
3. No dedicated client. `pip install requests` covers every pull. Paginate with `$skip` in steps of `$top` (max 10,000 per page) until you get a short batch.
4. No published rate limit, but OpenFEMA's docs ask for polite sequential access — don't parallel-hammer. A full 12-metric × 3-geo refresh at the NFIP national scale (~1M rows) is the slow leg; otherwise most pulls land in under a second.

## Minimal Python example

```python
import requests
from collections import defaultdict

# FEMA disaster declarations — Hillsborough County, FL, 2010+
url = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"
params = {
    "$filter": "state eq 'FL' and fipsCountyCode eq '057' and fyDeclared ge 2010",
    "$top": 10000,
    "$inlinecount": "allpages",
}
rows = requests.get(url, params=params, timeout=60).json()["DisasterDeclarationsSummaries"]
per_year = defaultdict(set)
for rec in rows:
    per_year[rec["fyDeclared"]].add(rec["disasterNumber"])
for year, ids in sorted(per_year.items()):
    print(f"{year}: {len(ids)} distinct disaster declarations")
```

Swap `fipsCountyCode eq '057'` for the Florida benchmark (drop the county clause) or drop both state + county clauses for national. Different datasets use different county field names + encodings — see Gotchas. For metrics beyond disaster declarations, grab the `api_endpoint` from `references/metrics.md` and adapt the snippet.

## The 4 categories

| Category | Purpose | Count |
|---|---|---|
| `disaster_frequency` | How often FEMA shows up: total declarations, hurricane-only subset | 2 |
| `flood_insurance` | NFIP market: claim count, paid $, avg severity, gross damage assessed | 4 |
| `individual_assistance` | Household-level disaster $: IHP total, owner IA, renter IA, registrations | 4 |
| `public_assistance` | Federal infrastructure rebuild $: PA federal obligation, permanent work share | 2 |

Total: 12 metrics. See `references/metrics.md` for the full list with `api_endpoint`s.

## Decision playbooks

Concrete "the user asked X — here's the metric set to pull." Use these as starting points; extend when the question demands it. If a playbook names a metric, `references/metrics.md` has the verbatim rationale.

**"How disaster-exposed is Hillsborough?"**
→ `fema_disaster_declarations_county`, `fema_hurricane_declarations_county`
Total declarations is the breadth read (hurricanes + severe storms + flood + biological); hurricane-only isolates the peril that actually drives Tampa insurance pricing. Run both against FL + US — in hurricane years Hillsborough runs hot; in quiet years it should track the nation.

**"What is flood insurance actually costing this county?"**
→ `fema_nfip_claims_count_county`, `fema_nfip_claims_paid_county`, `fema_nfip_avg_claim_paid_county`
Count is frequency, paid $ is magnitude, avg severity is the per-event cost. Watch count-vs-severity divergence: many small claims reads like routine cycles; fewer larger claims reads catastrophic. The paid-$ share of FL relative to Hillsborough's population share shows whether Tampa is subsidizing the state's NFIP pool in a given year.

**"Is the insurance market under-paying damage claims?"**
→ `fema_nfip_building_damage_assessed_county`, `fema_nfip_claims_paid_county`
Gross building damage (paid + denied) vs settled $ — widening spreads predict angrier policyholders and coverage-market stress. Investor-relevant as a coverage-gap signal before your own next renewal.

**"Who gets federal help when a storm hits here?"**
→ `fema_ihp_assistance_county`, `fema_ihp_owner_assistance_county`, `fema_ihp_renter_assistance_county`, `fema_disaster_registrations_county`
Total IHP is the dollar headline; owner/renter split captures the structural-vs-displacement axis of disaster loss; registrations count is the "how many households showed up" metric (broader than approvals). The ratio of IHP to NFIP paid tells you whether uninsured households or flood-insured homeowners took the brunt.

**"Is the rebuild actually happening or is it all cleanup?"**
→ `fema_pa_federal_obligation_county`, `fema_pa_permanent_work_share_county`
PA federal obligation = total infrastructure $ flowing to the county after a declared disaster. Permanent-work share (damage categories C–G) separates short-horizon emergency response (debris + protective measures, categories A–B) from long-horizon reinvestment (roads, water, utilities, buildings, parks). Permanent share running hot in a post-disaster year means the federal money is actually rebuilding, which supports long-term property values.

**"Tenant-displacement read after a major FL hurricane?"**
→ `fema_ihp_renter_assistance_county`, `fema_disaster_registrations_county`
Renter IA spiking means significant tenant-pool displacement — watch lease-renewal rate and concession requests in your portfolio for the next 1–2 quarters, that's where displacement cost actually lands on P&L. Registrations count gives the broader footprint (displaced + ineligible + denied households all file).

## Gotchas

- **Five distinct county-code encodings across FEMA datasets.** `DisasterDeclarationsSummaries` uses `fipsCountyCode='057'` (3-char zero-padded). `FimaNfipClaims` uses `countyCode='12057'` (5-char state+county FIPS). `PublicAssistanceFundedProjectsDetails` uses `countyCode='57'` — **unpadded**, no leading zeros (live testing confirmed `'057'` returns zero rows). `HousingAssistanceOwners` / `HousingAssistanceRenters` / `RegistrationIntakeIndividualsHouseholdPrograms` use `county='Hillsborough (County)'` — human-readable string, state filter mandatory to disambiguate from New Hampshire's Hillsborough (decision #110).
- **State filter field name varies: `state` vs `stateAbbreviation`.** The *value* is consistent (`'FL'`) across every FEMA dataset, but PA uses `stateAbbreviation` while DDS/NFIP/HAO/HAR/RegIntake use `state`. Catalog's `benchmark_geos[]` stores the value; per-source fetcher maps to the field (decision #111).
- **National predicate = absence of any state + county filter.** No special "US" flag; drop the geo clauses entirely and OpenFEMA returns every matching row nationwide. Large scans — NFIP national is ~1M rows, ~100 pages at 10k/page — but tractable on a fresh run.
- **Datasets without date fields on rows need a DDS join.** `HousingAssistanceOwners`, `HousingAssistanceRenters`, and `RegistrationIntakeIndividualsHouseholdPrograms` are pre-aggregated by disaster × city × zip but carry no `yearOfLoss` or `declarationDate`. Year resolution = join `disasterNumber` against `DisasterDeclarationsSummaries.fyDeclared`. One DDS prefetch per geo + in-memory lookup handles 4 downstream aggregators (decision #113).
- **RegIntake replaces the row-per-registration IHP dataset.** `IndividualsAndHouseholdsProgramValidRegistrations` returns one row per registration — ~500k rows for Hillsborough across years, ~54 pages. `RegistrationIntakeIndividualsHouseholdPrograms` is the pre-aggregated version with identical `ihpAmount` totals at ~2k rows (1 page). The catalog uses RegIntake; if you're rolling your own, do the same (decision #113).
- **Two relevant datasets explicitly out of scope.** `FimaNfipPolicies` is 72.5M rows — snapshot-date policies-in-force requires a dedicated data-engineering pipeline, not catalog-surface aggregation. `HazardMitigationAssistance*` endpoints returned 404 across every tested name variant as of 2026-04-20 — appear renamed or removed upstream. Skip both unless FEMA republishes (decision #114).
- **Null handling: treat as zero, not missing.** `amountPaidOnBuildingClaim`, `totalApprovedIhpAmount`, `federalShareObligated`, `ihpAmount`, `buildingDamageAmount` are all routinely null when the claim was denied / project unobligated. Aggregators coerce null → 0 for sum metrics, and NFIP avg severity treats zero-claim years as null (chart shows a gap, not a misleading zero).
- **Hurricane-only years will legitimately be zero.** `fema_hurricane_declarations_county` returns 0 for Hillsborough in quiet cycles (2013–2016 baseline). Not a data gap — a real signal. Chart renders legitimate zeroes, not nulls.
- **Window is 2010–2024.** DDS goes back to 1953 and IHP to 2002, but catalog-surface observations span 2010–2024 (15 years) for chart legibility across 3 geos. Captures post-Biggert-Waters NFIP reprice (2012), Sandy (2012), Harvey/Irma (2017), Michael (2018), Ian (2022), Helene/Milton (2024) — the full catastrophe cycle without pre-reform crowding. Partial-year 2025 rows excluded client-side (NFIP ~90-day lag, PA continuous, DDS near-real-time — consistent cutoff avoids per-dataset partial-year handling).
- **Keyless but polite.** OpenFEMA docs ask for sequential paginated GETs — don't parallelize page fetches across workers. A full refresh serializes cleanly in 15–20 minutes with the national NFIP pull being the slow leg.

## Source of truth

This skill is derived from TiRE's canonical catalog at [agents/data/fema-datasets.yaml](https://github.com/analyticsariel/tech-in-real-estate-ops/blob/main/agents/data/fema-datasets.yaml). The YAML is hand-curated; every entry has a `why_it_matters` rationale that feeds both this skill and TiRE's research agents.

When the upstream catalog changes, regenerate `references/metrics.md` and `references/fema-datasets.yaml`. v1 is hand-curated; build script deferred until drift is observed.
