# FRED Real-Estate Metrics — Full Reference

Load this file when a user asks about a specific FRED series, when a decision playbook in the parent `SKILL.md` points here, or when you need the `series_id` to pull.

All 44 series across 9 categories. Each entry: `key` · `series_id` · frequency · unit · what it signals. Ticker-tier series (the ones TiRE surfaces on its site marquee) are marked ★.

For a richer shape (tags, source publisher, FRED URL, notes), consult `references/fred-series.yaml` alongside this file.

## Table of contents

- [Rates & Financing](#rates--financing) — 7 series
- [Prices](#prices) — 7 series
- [Affordability](#affordability) — 1 series
- [Supply](#supply) — 7 series
- [Demand](#demand) — 4 series
- [Rental Market](#rental-market) — 5 series
- [Macro Labor](#macro-labor) — 5 series
- [Inflation](#inflation) — 4 series
- [Credit & Market Stress](#credit--market-stress) — 4 series

## Rates & Financing

- **★ mortgage_30y** · `MORTGAGE30US` · weekly (Thu) · % — Single most-watched number in RE. Every new purchase and refi calc starts here.
- **mortgage_15y** · `MORTGAGE15US` · weekly (Thu) · % — Refi math lives here. Spread to 30Y tells you which loan is cheaper.
- **★ treasury_10y** · `DGS10` · daily · % — Leads mortgage rates by days to weeks. If this moves, MORTGAGE30US follows.
- **treasury_2y** · `DGS2` · daily · % — Short end of the curve. Pair with DGS10 to read curve shape and recession signal.
- **fed_funds_daily** · `DFF` · daily · % — Daily read on the Fed's policy rate. Use when timeliness matters.
- **fed_funds_monthly** · `FEDFUNDS` · monthly · % — Policy anchor. Sets the direction for every other rate in the stack.
- **prime_rate** · `DPRIME` · daily · % — HELOC and bank loan pricing hinges on prime. Moves in lockstep with Fed funds + 300bps.

## Prices

- **★ median_home_price_existing** · `HOSMEDUSM052N` · monthly · $ — The headline "market" number every news anchor cites. Sets the mental anchor buyers and sellers walk into every negotiation with.
- **median_home_price_sf** · `HSFMEDUSM052N` · monthly · $ — Single-family only. Cleaner read for SFR investors than the all-types median.
- **median_new_home_price** · `MSPNHSUS` · monthly · $ — New construction pricing. Diverges from existing-home median in supply-constrained cycles.
- **median_listing_price** · `MEDLISPRIUS` · monthly · $ — What sellers ask for, not what clears. Gap vs. sold price reveals buyer leverage.
- **case_shiller_national** · `CSUSHPINSA` · monthly · index — National price trajectory. Says whether "prices are flat/falling/rising" is actually true. ~2-month lag, Jan 2000 = 100.
- **case_shiller_20** · `SPCS20RSA` · monthly · index — 20 largest metros, weighted by market size. More sensitive than the national series. ~2-month lag.
- **fhfa_hpi** · `USSTHPI` · quarterly · index — Purchase-only alt to Case-Shiller. When CS and FHFA disagree, something odd is happening. Conforming loans only.

## Affordability

- **★ housing_affordability_index** · `FIXHAI` · monthly · index — Fuses rates + prices + incomes into one number. 100 = median family can just afford median home. ⚠ FRED only retains the trailing 13 months per NAR's data agreement; pull history elsewhere.

## Supply

- **★ housing_starts** · `HOUST` · monthly · thousands (SAAR) — Forward supply. Falls → future inventory squeeze → prices and rents firm up.
- **housing_starts_sf** · `HOUST1F` · monthly · thousands (SAAR) — Isolates SFR pipeline from multi-family noise. The number that matters if you buy houses.
- **building_permits** · `PERMIT` · monthly · thousands (SAAR) — Earlier than starts. First look at what supply looks like in 6–12 months.
- **building_permits_sf** · `PERMIT1` · monthly · thousands (SAAR) — Earliest signal of SFR supply pipeline. Builders commit to permits before they break ground.
- **housing_completions** · `COMPUTSA` · monthly · thousands (SAAR) — When supply actually hits the market. Lags starts by ~6–12 months.
- **★ months_supply_new** · `MSACSR` · monthly · ratio — Ratio of new inventory to sales pace. >6 = buyer's market; <4 = seller's.
- **active_listings** · `ACTLISCOUUS` · monthly · count — Raw count of homes for sale nationally. Direct read on inventory tightness. Coverage begins 2016-07.

## Demand

- **existing_home_sales** · `EXHOSLUSM495S` · monthly · millions (SAAR) — Liquidity signal. How fast you can close and how motivated sellers are.
- **existing_sf_home_sales** · `EXSFHSUSM495S` · monthly · millions (SAAR) — SFR slice of transaction volume. Use when condos and co-ops would muddy the read.
- **new_home_sales** · `HSN1F` · monthly · thousands (SAAR) — Demand at the new-construction end. Leads resale price moves.
- **★ median_days_on_market** · `MEDDAYONMARUS` · monthly · days — Time to sell. Falling = fast market, tight inventory; rising = inventory stacking up. Coverage begins 2016-07.

## Rental Market

- **★ cpi_rent_primary** · `CUSR0000SEHA` · monthly · index — BLS's national rent inflation. Cross-check your local rent raises against this. Index only — FRED has no clean $-value national median rent (Zillow ZORI is off-FRED).
- **cpi_owners_equivalent_rent** · `CUSR0000SEHC01` · monthly · index — BLS's imputed rent for owners. Biggest component of core CPI — Fed watches this closely.
- **★ rental_vacancy_rate** · `RRVRUSQ156N` · quarterly · % — Direct read on rent pricing power. Low vacancy = you can raise rent.
- **homeowner_vacancy_rate** · `RHVRUSQ156N` · quarterly · % — Empty homes for sale. Rising = price weakness; falling = tight market.
- **homeownership_rate** · `RHORUSQ156N` · quarterly · % — Down = more renters. Direction signal for rental demand.

## Macro Labor

- **★ unemployment_rate** · `UNRATE` · monthly · % — Tenants without jobs don't pay rent. Leading signal for rent-collection risk.
- **nonfarm_payrolls** · `PAYEMS` · monthly · thousands — Labor strength. Strong = rent affordability strong = demand intact.
- **employment_population_ratio** · `EMRATIO` · monthly · % — Share of adults with a job. Cleaner than UNRATE when labor-force participation is shifting.
- **real_disposable_income** · `DSPIC96` · monthly · $ (chained 2017, SAAR) — After-inflation spending power. Tells you whether tenants can absorb rent raises.
- **real_median_household_income** · `MEHOINUSA672N` · annual · $ — Annual benchmark for income growth. Anchor for affordability math over multi-year horizons. Released with ~9-month lag.

## Inflation

- **cpi_all_items** · `CPIAUCSL` · monthly · index — Headline inflation. What you're being paid back in when you hold a fixed-rate mortgage.
- **core_cpi** · `CPILFESL` · monthly · index — What the Fed actually watches. Predicts rate path, which predicts mortgage rates.
- **pce** · `PCEPI` · monthly · index — The Fed's preferred inflation gauge — their 2% target is defined against this, not CPI.
- **core_pce** · `PCEPILFE` · monthly · index — The single number the Fed cares about most. Directly drives rate-cut/hike decisions.

## Credit & Market Stress

- **sfr_delinquency_rate** · `DRSFRMACBS` · quarterly · % — Market-stress signal. Rising delinquency = distress inventory coming.
- **sfr_chargeoff_rate** · `CORSFRMACBS` · quarterly · % — Confirmed losses. When this follows delinquencies up, the cycle is real.
- **household_debt_service_ratio** · `TDSP` · quarterly · % — How stretched households are. High = rent-raise ceiling; low = headroom for demand.
- **cre_chargeoff_rate** · `CORCREXFACBS` · quarterly · % — CRE stress bleeds into small-bank balance sheets — and small banks finance SFR rentals.
