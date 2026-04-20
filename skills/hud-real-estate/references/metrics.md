# HUD Real-Estate Metrics — Full Reference

Load this file when a user asks about a specific HUD metric, when a decision playbook in the parent `SKILL.md` points here, or when you need the extractor / variable code to pull.

All 12 metrics across 3 categories. Each entry: `dataset_key` · extractor (or CHAS derivation) · frequency · unit · verbatim rationale (lifted from the canonical catalog).

Geography default is Hillsborough County, FL — HUD entityid `1205799999` for FMR/IL/MTSP IL, CHAS parameters `type=3&stateId=12&entityId=57`. Benchmarks bifurcate by endpoint: FMR none, IL Florida only (via `/il/statedata/FL`), CHAS Florida (`type=2&stateId=12`) + US (`type=1`). No national AMI exists.

For a richer shape (full Python snippets, `benchmark_geos[]` blocks, notes), consult `references/hud-datasets.yaml` alongside this file.

## Table of contents

- [Rent Ceilings (FMR)](#rent-ceilings-fmr) — 2 metrics
- [Income Limits](#income-limits) — 5 metrics
- [Housing Needs (CHAS)](#housing-needs-chas) — 5 metrics

## Rent Ceilings (FMR)

Fair Market Rent — the legal voucher payment ceiling under Section 8. All FMR entries pull from `/fmr/data/1205799999?year=YYYY` (one call returns all 5 bedroom sizes). Extract from `data.basicdata` where `zip_code == "MSA level"`. No state/national benchmarks — HUD assigns FMR at MSA level, not above. The backend bedroom archive (`site/data/archive/hud/fmr_bedroom_breakout.json`) captures all 5 bedroom values every snapshot run even though the site features only 2BR + 3BR.

- **hud_fmr_2br** · `row["Two-Bedroom"]` · annual · dollars

  The default FMR number. When someone says "what's the voucher rent on a 2BR in Tampa," this is the answer. It's also the 2BR comp every lender will accept as a defensible market anchor — HUD publishes a fresh survey every FY and writes the methodology out in the open.

- **hud_fmr_3br** · `row["Three-Bedroom"]` · annual · dollars

  The SFR tier. Most 1-to-3-property operators are buying 3-bedroom single-family homes, and this is the FMR that applies when you take a voucher on one. Pairs with ACS median gross rent (`census_median_gross_rent`) — if FMR is above median rent, voucher tenants are a premium; if below, they're a discount to market.

## Income Limits

4 standard IL tiers (`/il/data`) + 1 MTSP IL tier (`/mtspil/data`). Same Bearer auth across both endpoints. 4-person household is the HUD-standard reference; all entries ship with a Florida benchmark via `/il/statedata/FL?year=YYYY` except MTSP IL (which has no statedata endpoint — 404s on `/mtspil/statedata/FL`). No national AMI — definitionally local.

- **hud_il_ami** · `data["median_income"]` · annual · dollars · `/il/data`

  The reference every "% of AMI" conversation anchors on. HUD's 4-person AMI is the denominator behind the 30/50/80% tiers; chasing market rent above AMI / 40 tells you the deal sits past what local incomes can absorb. Tracked against Florida to see whether Hillsborough is pulling ahead of state income growth or falling behind.

- **hud_il_30ami_4person** · `data["extremely_low"]["il30_p4"]` · annual · dollars · `/il/data`

  The extremely-low-income threshold — federal definition of households most at-risk for eviction and the qualifying line for LIHTC's 30% basis boost and several HUD rental programs. If you're underwriting deep-affordable, this is where the rent caps come from. If you're market-rate, it's a useful floor for "how poor is too poor to be a target tenant" in a specific county.

- **hud_il_50ami_4person** · `data["very_low"]["il50_p4"]` · annual · dollars · `/il/data`

  The Section 8 voucher eligibility base — a household below 50% AMI is the default voucher target. This is also the rent-cap anchor for LIHTC 50% AMI units and the qualifying line for Section 202 / 811 programs. For a 1-to-3-property investor underwriting voucher tenants, this is the number that says "will my target resident actually qualify at my target rent?"

- **hud_il_80ami_4person** · `data["low"]["il80_p4"]` · annual · dollars · `/il/data`

  The "low-income" ceiling. A household below this qualifies for most affordable-housing programs, some down-payment assistance, and LIHTC 80% AMI units. For a tech investor: any working-class tenant in your Tampa rental pool is almost certainly under this line, and it defines the top of the demand pool most affordable-housing programs compete for.

- **hud_mtspil_60ami_4person** · `data["60percent"]["il60_p4"]` · annual · dollars · `/mtspil/data`

  The LIHTC rent-cap anchor. Most Florida LIHTC projects underwrite at the 60% AMI set-aside — rent cannot exceed 30% of this income figure (minus a utility allowance). If you're tracking LIHTC supply in your market, this is the income line that sets the ceiling; if you're underwriting a tax-credit deal directly, this is the number your rent schedule keys off.

## Housing Needs (CHAS)

Custom tabulations of ACS data that ACS 5-Year alone can't answer — cost burden crossed with tenure and income. All entries pull from `/chas?type=3&stateId=12&entityId=57&year=YYYY-YYYY` with native benchmarks via `type=2&stateId=12` (FL) and `type=1` (US). CHAS vintages = 5-year ACS windows; current: `2018-2022`, `2017-2021`, `2016-2020`, `2015-2019`, `2014-2018`. **CHAS API returns numeric counts as strings — cast with `float()` before arithmetic.**

Variable coding uses `A1-J17` (132 vars across 10 groups A-J). This is **different from** the `T{n}_est*` codes in HUD's CSV-download CHAS data-dictionary spreadsheet. Sprint 13 uses Groups A (Income × Occupancy) and D (Cost Burden × Occupancy direct) for flat, stable derivations.

- **hud_chas_renter_severe_cost_burden** · `D8 / A17 × 100` · annual · percent

  The renter-distress gauge. A household paying more than half its income on rent has no buffer — one car repair away from late rent, one job loss from eviction. Above ~25% this is a wide renter pool under real strain, which caps your rent-push headroom and raises delinquency risk. Track it against Florida and the US to see whether Hillsborough's distress is local or a national pattern.

- **hud_chas_owner_cost_burden** · `(D4 + D7) / A16 × 100` · annual · percent

  The homeowner mirror of renter cost burden. This is the share of mortgaged-plus-free-and-clear owners spending over 30% of income on housing — an insurance-and-tax stress gauge that rose fast in Florida post-2022 as HOAs, property insurance, and assessments hit. If owner cost burden is climbing while your acquisition thesis assumes "owners are comfortable," that's a reprice-risk signal for the for-sale market.

- **hud_chas_renter_households_below_80ami** · `A2 + A5 + A8` · annual · count

  The size of the qualifying demand pool for every affordable-housing program in the county. If you're underwriting voucher, LIHTC, or workforce-housing strategies, this is your addressable market. Benchmarked against Florida + US so you can tell whether Hillsborough has a proportionally bigger or smaller eligible renter base than the surrounding baseline — relevant for voucher-concentration risk and for scoping affordable inventory gaps.

- **hud_chas_renter_severe_housing_problems** · `C2 / A17 × 100` · annual · percent

  The distress signal that cost burden alone doesn't catch. A unit with bad plumbing or a kitchen the tenant can't cook in is a housing problem before rent-to-income even enters the conversation. This metric captures those plus severe cost burden in one number — a broader measure of "tenants living in unacceptable conditions." Above ~30% is a wide renter pool that reads as a rehab-opportunity signal or a concentration-of-distress risk depending on which side of the deal you're on.

- **hud_chas_extremely_low_income_renters** · `A2` · annual · count

  The priority-tenant pool. Every HUD rental program — voucher, Section 8, LIHTC 30% basis bonus, Section 202/811 — uses this line as the first eligibility check. Size of this pool tells you how many households in the county are HUD-priority-eligible; trend tells you whether deep-affordable demand is compressing or expanding. If you're underwriting a voucher-concentrated strategy, this is your addressable universe.

## CHAS A-J group quick-reference (API coding)

Read-around when a playbook asks for a group cell this skill doesn't wrap.

- **A** — Household Income × Occupancy. A1-A15 = 5 income tiers × 3 occupancy cuts (owner/renter/total per tier). A16 = owner total, A17 = renter total, A18 = grand total.
- **B** — At least 1 of 4 housing problems × Occupancy. Same B1-B6 layout as A's first 6.
- **C** — At least 1 of 4 **severe** housing problems × Occupancy. C1-C6 same layout.
- **D** — Cost Burden × Occupancy direct. D1/D2/D3 = CB≤30% (owner/renter/total); D4-D6 = CB 30.1-50%; D7-D9 = CB >50%; D10-D12 = CB not computed.
- **E, F, G** — Income × Housing Problems × Occupancy (E = combined, F = renter, G = owner). Sparse — many cells null.
- **H** — Income × Cost Burden × Combined tenure.
- **I, J** — Income × Cost Burden × Renter / Owner split. Sparse on the >50% column.

Use Groups A + D for flat derivations when you can — they're stable across vintages and don't fan out per income tier.
