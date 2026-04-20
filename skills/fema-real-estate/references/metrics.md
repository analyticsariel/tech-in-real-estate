# FEMA Real-Estate Metrics — Full Reference

Load this file when a user asks about a specific FEMA metric, when a decision playbook in the parent `SKILL.md` points here, or when you need the `api_endpoint` to pull.

All 12 metrics across 4 categories, sourced from OpenFEMA v2 (keyless). Each entry: `key` · OpenFEMA dataset · `$filter` template (Hillsborough County primary) · frequency · unit · verbatim rationale (lifted from the canonical catalog).

Geography default is Hillsborough County, FL (FIPS `12057`), with Florida (state `FL`) + United States (no-geo) benchmarks per metric. Swap the primary-county clause for the state clause to benchmark against Florida; drop both for national. Filter-field names and county-code encodings vary by dataset — see the parent `SKILL.md` Gotchas section or the catalog YAML.

For a richer shape (full `api_endpoint` URLs, benchmark geographies, copy-pasteable Python snippets, fetcher derivation notes), consult `references/fema-datasets.yaml` alongside this file.

## Table of contents

- [Disaster Frequency](#disaster-frequency) — 2 metrics
- [Flood Insurance (NFIP)](#flood-insurance-nfip) — 4 metrics
- [Individual Assistance](#individual-assistance) — 4 metrics
- [Public Assistance](#public-assistance) — 2 metrics

## Disaster Frequency

- **fema_disaster_declarations_county** · `DisasterDeclarationsSummaries` · `state eq 'FL' and fipsCountyCode eq '057' and fyDeclared ge 2010` · annual · count

  The clearest free read on "how often does FEMA show up here." A county's annual count of federally declared disasters tracks the hurricane, flood, and severe-storm events that insurers price off. Against FL + US benchmarks you can see whether Hillsborough runs hot vs the state and nation — in hurricane years it will, in quiet years it shouldn't.

- **fema_hurricane_declarations_county** · `DisasterDeclarationsSummaries` · `state eq 'FL' and fipsCountyCode eq '057' and incidentType eq 'Hurricane' and fyDeclared ge 2010` · annual · count

  Tampa's disaster story is mostly hurricanes. Splitting hurricane declarations out from the full declaration count isolates the signal that actually drives premium increases, roof replacements, and buyer hesitancy — biological emergencies and severe storms matter but don't dictate homeowners insurance the way a landed hurricane does. Zero-years are legitimate data, not gaps: quiet cycles exist.

## Flood Insurance (NFIP)

- **fema_nfip_claims_count_county** · `FimaNfipClaims` · `state eq 'FL' and countyCode eq '12057' and yearOfLoss ge 2010` · annual · count

  Every NFIP claim is a flood that insurers actually paid on. Claim counts by year are the truth-teller for flood frequency: if Hillsborough's volume is stepping up decade over decade while FL + US stay flat, that's local risk drift showing up in policy-level data. Indexed-mode chart (first year = 100) because US claims (~50k/yr) would flatten Hillsborough (~500/yr) to a smear.

- **fema_nfip_claims_paid_county** · `FimaNfipClaims` · `state eq 'FL' and countyCode eq '12057' and yearOfLoss ge 2010` · annual · dollars

  Dollars settled on NFIP flood policies — the tangible climate bill the local insurance market is absorbing. A year with $200M+ in Hillsborough NFIP payouts is a year that hits every policyholder's next renewal, insured or not (NFIP reinsurance losses flow through to private markets). Benchmark against FL + US: when Tampa's payout share of the state exceeds its population share, Tampa is subsidizing FL's flood-insurance pool in that year.

- **fema_nfip_avg_claim_paid_county** · `FimaNfipClaims` · `state eq 'FL' and countyCode eq '12057' and yearOfLoss ge 2010` · annual · dollars

  Severity tells a different story than frequency. A year with many small claims reads like a routine flood cycle; a year with fewer larger claims reads like a catastrophic event. When Hillsborough's avg payout spikes vs FL + US in the same year, that's structurally severe damage — the kind that reprices reinsurance and ultimately your homeowners premium.

- **fema_nfip_building_damage_assessed_county** · `FimaNfipClaims` · `state eq 'FL' and countyCode eq '12057' and yearOfLoss ge 2010` · annual · dollars

  Gross building damage (paid + denied) is the scope-of-loss number, not the settlement number. A year where gross damage runs hot but paid $ runs cool means insurers are denying or under-paying claims — investor-relevant as a signal of coverage-gap risk at your own property. Watch the spread between paid $ and assessed damage over time; widening spreads predict angrier policyholders and coverage-market stress.

## Individual Assistance

- **fema_ihp_assistance_county** · `RegistrationIntakeIndividualsHouseholdPrograms` · `state eq 'FL' and county eq 'Hillsborough (County)'` · annual · dollars

  Federal dollars that flowed directly to Hillsborough households after disasters — rent assistance, repair grants, replacement checks. This is the renters-and-uninsured half of the climate-cost ledger; NFIP captures the homeowner-with-flood-policy half. Watch the ratio of IHP $ to NFIP paid $: when IHP runs hotter, the damage is falling on households without private coverage.

- **fema_ihp_owner_assistance_county** · `HousingAssistanceOwners` · `state eq 'FL' and county eq 'Hillsborough (County)'` · annual · dollars

  Owner IA dollars are federal checks to homeowners for repair, replacement, and temporary-housing costs when insurance doesn't fully cover the damage. If owner IA runs hot in Hillsborough vs FL, it means the county's insured-homeowner coverage gap is wider than the state average — a structural signal about which neighborhoods have the weakest private insurance uptake.

- **fema_ihp_renter_assistance_county** · `HousingAssistanceRenters` · `state eq 'FL' and county eq 'Hillsborough (County)'` · annual · dollars

  Renter IA captures the displacement half of disaster cost — rental assistance, lodging aid, replacement personal-property grants for tenants who lost housing. Investors with single-family rentals or small multifamily should read this next to owner IA: a disaster year where renter IA spikes tells you the tenant pool in your county absorbed more displacement risk than the owner-occupant pool did. That pressure shows up later as tenant turnover and lease-up delays.

- **fema_disaster_registrations_county** · `RegistrationIntakeIndividualsHouseholdPrograms` · `state eq 'FL' and county eq 'Hillsborough (County)'` · annual · count

  Registration count is the "how many households showed up" metric — broader than approved dollars because it includes denied and ineligible filings. Against FL + US, a year where Hillsborough's registration share spikes vs. its population share tells you the disaster footprint hit this county harder than average regardless of how much federal money ended up flowing.

## Public Assistance

- **fema_pa_federal_obligation_county** · `PublicAssistanceFundedProjectsDetails` · `stateAbbreviation eq 'FL' and countyCode eq '57' and declarationDate ge '2010-01-01T00:00:00.000Z'` · annual · dollars

  Public Assistance is the federal money that rebuilds county infrastructure after a declared disaster — roads, water systems, parks, schools, public buildings. When Hillsborough's PA obligation spikes in a disaster year, that's infrastructure spend that raises the floor under long-term property values and says something quantitative about how bad the damage actually was. Watch the shape against FL + US: Florida's PA cycle dominates US totals in hurricane years.

- **fema_pa_permanent_work_share_county** · `PublicAssistanceFundedProjectsDetails` · `stateAbbreviation eq 'FL' and countyCode eq '57' and declarationDate ge '2010-01-01T00:00:00.000Z'` · annual · percent

  Permanent-work share tells you whether the county is rebuilding or just cleaning up. Emergency work (debris + protective measures, damage categories A–B) is the short-horizon cost; permanent work (roads, utilities, buildings, parks, categories C–G) is the long-horizon reinvestment that recovers property values. A year with high PA dollars but low permanent share is immediate-response-heavy; a year where permanent share runs hot is when the federal money is actually rebuilding the county. At county grain the share is lumpy year-over-year; compare against FL + US trend lines rather than reading any single year.
