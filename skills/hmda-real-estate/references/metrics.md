# HMDA Real-Estate Metrics — Full Reference

Load this file when a user asks about a specific HMDA metric, when a decision playbook in the parent `SKILL.md` points here, or when you need the `api_endpoint` to pull.

All 14 metrics across 6 categories, sourced from the CFPB HMDA Data Browser aggregations endpoint. Each entry: `key` · `api_endpoint` (Hillsborough County template) · frequency · unit · verbatim rationale (lifted from the canonical catalog).

Geography default is Hillsborough County, FL (FIPS `12057`), with Florida (state `FL`) + United States (51-state rollup) benchmarks per metric. Swap the `counties=12057` query arg for `states=FL` (Florida) or the full 51-state comma-joined list for national — per decision #94, there is no no-geo mode. Every URL below returns JSON with an `aggregations[]` array carrying `{count, sum, <group_field>}` per bucket; the fetcher in `agents/sources/hmda.py` knows which field to read per metric.

For a richer shape (benchmark geographies, copy-pasteable Python snippets, fetcher derivation notes), consult `references/hmda-datasets.yaml` alongside this file.

## Table of contents

- [Credit Access](#credit-access) — 3 metrics
- [Loan Purpose / Refi Cycle](#loan-purpose--refi-cycle) — 3 metrics
- [Product Mix](#product-mix) — 3 metrics
- [Volume & Size](#volume--size) — 2 metrics
- [Property Type](#property-type) — 2 metrics
- [Fair Lending](#fair-lending) — 1 metric

## Credit Access

- **hmda_originations_count** · `?years={year}&counties=12057&actions_taken=1` · annual · count

  FRED tells you what rate banks are quoting; this tells you how many Hillsborough borrowers actually closed. When originations fall off a cliff, it's the flow signal that leads the price signal — buy-side demand softens before sellers cut list. Benchmark against Florida and US: if Tampa originations are dropping faster than the state, your market is cooling on its own, not just riding a national cycle.

- **hmda_application_count** · `?years={year}&counties=12057&actions_taken=1,2,3,4,5` · annual · count

  Applications lead originations by about a quarter — borrowers file first, close second. Watch this before the originations line moves: if apps are cliff-diving while originations look stable, the next quarter's closing volume is already pre-written. Vs FL and US: when Hillsborough apps fall faster than the state, it's a local demand story — jobs, migration, affordability — not just the macro rate cycle.

- **hmda_denial_rate** · `?years={year}&counties=12057&actions_taken=1,2,3,4,5` · annual · percent

  Rising denial rates mean lenders are tightening — that's a leading read on how hard your next refi exit is going to be, and how much buyer demand evaporates before the Fed's rate move shows up in Redfin's weekly price feed. Versus FL + US: when Hillsborough denials climb faster than the state, local underwriting is reacting to something specific (insurance loss, condo assessments, migration reversal).

## Loan Purpose / Refi Cycle

- **hmda_purchase_share** · `?years={year}&counties=12057&actions_taken=1&loan_purposes=1,31,32` · annual · percent

  When rates are low, the refi line takes over and purchase share craters; when rates are high, refi dies and purchase is most of what's left. The swing between the two is the cleanest read on where the mortgage market is in the cycle. Versus FL + US: Hillsborough running higher purchase share than the nation means net in-migration is still pulling transaction volume toward real sales rather than existing-owner refinance activity.

- **hmda_refi_count** · `?years={year}&counties=12057&actions_taken=1&loan_purposes=31,32` · annual · count

  The most rate-sensitive line on the page. When the 30-year drops 50 bps, this line explodes; when it climbs 50 bps, this line collapses. Tracks the health of existing-owner equity extraction and rate-cycle timing. Versus FL + US: when Hillsborough refis swing harder than the nation, you're seeing the concentrated effect of Florida's above-average equity cushion meeting rate changes.

- **hmda_cashout_refi_share** · `?years={year}&counties=12057&actions_taken=1&loan_purposes=31,32` · annual · percent

  When owners pull equity en masse, it reads two ways: either they've got real appreciation to cash out against, or they need liquidity and the house is the bank. Either way, cash-out share climbing above the rate-term refi line is a late-cycle signal. Benchmark against FL + US: Florida has historically run hotter on cash-out share (retirement liquidity, investor equity redeployment) — Hillsborough tracking above even that baseline is concentrated equity extraction worth watching against Redfin's price-cut trajectory.

## Product Mix

- **hmda_fha_share** · `?years={year}&counties=12057&actions_taken=1&loan_types=1,2,3,4` · annual · percent

  FHA is the 3.5%-down, government-backed, low-credit-floor product — it's where the marginal affordability buyer lives. When FHA share climbs, the median borrower in your county is leaning on federal backing to close, which is a leading affordability-stress signal and a soft-landing risk if rates move against them at refi. Versus FL + US: Hillsborough tracking higher than the national FHA share means the entry-level market's doing heavier lifting than the conventional market here. Purchase-vs-refi cycle effects live in hmda_purchase_share; this metric isolates product mix at the origination level.

- **hmda_va_share** · `?years={year}&counties=12057&actions_taken=1&loan_types=1,2,3,4` · annual · percent

  VA loans are zero-down, no-PMI, veteran-only. Their share is a function of local military presence and active-duty buyer demand, not affordability cycles — makes it a stable structural indicator rather than a cyclical one. Tampa's MacDill AFB anchors unusually high VA share here; watch FL + US deltas to see whether base-driven demand is holding up or the military buyer is being priced out.

- **hmda_conventional_share** · `?years={year}&counties=12057&actions_taken=1&loan_types=1,2,3,4` · annual · percent

  Conventional is everything that isn't FHA, VA, or USDA — the "real credit" product that requires 5–20% down and prime-adjacent credit. Its share is the inverse of government-backed product penetration: when conventional dominates, the borrower base is stronger; when it recedes, the marginal borrower is using federal backing to get across. Versus FL + US: Hillsborough running below the US conventional line is the affordability-stress read; running above is the opposite.

## Volume & Size

- **hmda_loan_volume** · `?years={year}&counties=12057&actions_taken=1` · annual · billions

  Volume in dollars is count × average loan size — it moves when either moves. When volume falls but count holds, loan sizes are shrinking (affordability pressure); when count falls but volume holds, the remaining buyers are at the higher end (selective market). Versus FL + US: Hillsborough's volume trajectory vs. state/nation tells you whether capital is flowing into this market faster or slower than the broader real-estate economy.

- **hmda_avg_purchase_loan_amount** · `?years={year}&counties=12057&actions_taken=1&loan_purposes=1` · annual · dollars

  Mean, not median — sensitive to the high end of the distribution. But that sensitivity is useful: when the mean moves up fast while Redfin's median sale price moves slowly, it's jumbo buyers doing the work (wealthy migrants, move-up trades). When the mean stagnates while prices climb, the low end is pulling harder than the top. Versus FL + US: Hillsborough tracking below the state mean is the affordability story; above it is the migration-pressure story.

## Property Type

- **hmda_small_multi_share** · `?years={year}&counties=12057&actions_taken=1&total_units=2,3,4` · annual · percent

  2-to-4-unit is where house hackers and small-portfolio operators live — the product most relevant to TiRE's audience (tech investors with 1–3 properties scaling up). Its share is typically a fraction of a percent, and the delta against FL + US tells you whether your county is competitive for this niche or dominated by single-family. Rising share usually tracks with missing-middle zoning wins and 2-to-4-unit financing-program uptake.

- **hmda_manufactured_share** · `?years={year}&counties=12057&actions_taken=1&construction_methods=2` · annual · percent

  Manufactured housing is the cheapest way to get into homeownership in many US counties, and it's an underbuilt category Florida has structurally more of than most states. A rising manufactured share is often a demand-side story: site-built supply priced out, buyers step down to manufactured to get under the affordability line. Versus FL + US: Hillsborough tracking above the national share with Florida even higher above it signals Florida's manufactured-friendly zoning + age-restricted community inventory.

## Fair Lending

- **hmda_black_applicant_denial_rate** · `?years={year}&counties=12057&actions_taken=1,2,3,4,5&races=Black%20or%20African%20American` · annual · percent

  A single fair-lending metric, reported against the same FL + US benchmarks as every other HMDA line. Tells the reader what the denial rate looks like for one applicant group — no composite index, no gap-of-gaps math. Compared cleanly across geographies, the question the data can answer is: is access in Hillsborough converging toward, or diverging from, the state and national patterns for this group? Read alongside hmda_denial_rate to see the same applicant pool's experience against the overall pool.
