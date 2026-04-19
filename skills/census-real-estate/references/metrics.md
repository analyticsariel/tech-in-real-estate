# Census Real-Estate Metrics — Full Reference

Load this file when a user asks about a specific ACS dataset, when a decision playbook in the parent `SKILL.md` points here, or when you need the ACS variable ID to pull.

All 12 datasets across 5 categories. Each entry: `dataset_key` · ACS variable or table ID · frequency · unit · verbatim rationale (lifted from the canonical catalog).

Geography default is Hillsborough County, FL (GEOID 12057), with Florida (state:12) + United States (us:1) benchmarks per dataset. Swap `for=county:057&in=state:12` for the geography you need — the ACS API takes county, state, metro, place, tract, and block-group predicates.

For a richer shape (table IDs, derivation formulas, benchmark config, notes), consult `references/census-datasets.yaml` alongside this file.

## Table of contents

- [Demographics](#demographics) — 3 datasets
- [Income & Affordability](#income--affordability) — 2 datasets
- [Housing Costs](#housing-costs) — 3 datasets
- [Tenure & Vacancy](#tenure--vacancy) — 2 datasets
- [Housing Stock](#housing-stock) — 2 datasets

## Demographics

- **census_population** · `B01003_001E` · annual · count

  The denominator behind every market-size argument. Year-over-year growth here is the most reliable leading indicator that a market's rents and prices have room to run. Compare Hillsborough's trajectory to Florida and the US to see whether demand is local-hot or a rising-tide effect.

- **census_bachelors_or_higher** · `B06009_001E`, `B06009_005E`, `B06009_006E` (derived) · annual · percent

  The single education number that predicts long-run rent and price growth. Bachelor's-share momentum is the leading indicator of high-income inflow and gentrification — pair with population growth to triangulate demand. Benchmark against state + national to see if Hillsborough is drawing educated inflow faster than the surrounding baseline.

- **census_labor_force_participation** · `B23025_001E`, `B23025_007E` (derived) · annual · percent

  The economic-engagement gauge. High LFPR = strong job market pulling adults into paid work; falling LFPR = retirees, students, or discouraged workers expanding. For a rental investor, LFPR predicts rent-payment capacity in aggregate — a county with falling LFPR has a thinner employed-renter pool. Benchmark against FL + US to distinguish local conditions from Sunbelt retirement drift.

## Income & Affordability

- **census_median_income** · `B19013_001E` · annual · dollars

  The demand-side ceiling for what you can charge in rent. Apply the 30%-of-income rule (divide by 40) and you have the local rent comp ceiling — pair with median rent to know if you have room to push. Hillsborough vs Florida vs US tells you whether a market's rent is priced to local income or imported demand.

- **census_median_rent_burden** · `B25071_001E` · annual · percent

  The single number that tells you whether rent has more room to run in this market. Median rent burden rises when rent outpaces income; it falls when incomes catch up. Above 30% is federally-defined "cost-burdened" — once the local median crosses that threshold, further rent push meets real income resistance. Benchmark against FL + US to see whether Hillsborough renters are more or less stretched than the baseline.

## Housing Costs

- **census_median_home_value** · `B25077_001E` · annual · dollars

  The headline wealth proxy. Anchors every "is this market expensive" question, sets the cap-rate math denominator, and defines the mortgage amount you'd underwrite against. Hillsborough vs Florida vs US shows whether the county commands a price premium or discount — and tracks whether that gap is widening or closing across vintages.

- **census_median_gross_rent** · `B25064_001E` · annual · dollars

  The revenue side of every SFR underwrite in this market. Gross rent (includes utilities, unlike B25031 contract rent) is the investor-standard comparison number. Pair with median household income for rent-burden math and with median home value for rent-to-price ratios. Benchmark against Florida and US to see whether Hillsborough rents are local-market or pulled up by statewide/coastal pressures.

- **census_median_owner_costs** · `B25088_001E` · annual · dollars

  The symmetric pair to median gross rent — "what does a mortgaged owner actually pay monthly" across all categories (P&I, taxes, insurance, utilities, HOA). Close to median rent + utilities means rent-vs-buy is a coin flip; far above means renting is the better deal. Hillsborough vs Florida vs US reads whether Tampa carries a cost premium or runs cheaper than the surrounding baseline.

## Tenure & Vacancy

- **census_homeownership_rate** · `B25003_001E`, `B25003_002E` (derived) · annual · percent

  The mix signal for a rental investor. High homeownership means the rental pool is shallow (fewer renters competing for units, but also fewer units on the rental market); low homeownership means a big renter base supports liquidity and leasing velocity. The trend direction matters as much as the level — falling ownership often precedes rent pressure. Benchmark against FL + US to find markets that deviate from the national equilibrium.

- **census_vacancy_rate** · `B25002_001E`, `B25002_003E` (derived) · annual · percent

  The supply-pressure gauge. Low vacancy (under ~7%) means tight market: rents push, leasing time-on-market compresses, operator leverage rises. High vacancy (above ~12%) flips the dynamic — concessions return, days-on-market stretches, and cap rates soften. The ACS vacancy rate captures both rental and for-sale inventory, so it's a broader read than Realtor's listed-inventory metric. Benchmark against FL + US to distinguish local tightness from regional/national cycle state.

## Housing Stock

- **census_housing_units** · `B25034_001E` · annual · count

  The scale denominator. Tells you whether the rental market you're entering is 400k units or 4M units — affects comp density, data reliability, and competitive dynamics. Growth rate year-over-year is the cleanest supply-addition indicator (new construction net of demolitions). In indexed mode the chart shows Hillsborough's housing stock growth vs Florida vs US — expanding faster or slower than the baseline.

- **census_median_year_built** · `B25035_001E` · annual · year

  A capex proxy at the market level. Older median year = higher expected maintenance costs, more deferred-maintenance comp risk, more opportunity for value-add. Newer median year = lighter capex assumptions but tighter cap rates. Shifts slowly (a metro's housing stock doesn't re-age year-to-year) so watch the benchmark gap — if Hillsborough's stock is aging faster than Florida's, construction is lagging demolition/growth.
