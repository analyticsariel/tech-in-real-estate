# Zillow Real-Estate Metrics — Full Reference

Load this file when a user asks about a specific Zillow series, when a decision playbook in the parent `SKILL.md` points here, or when you need the `dataset_key` or CSV URL to pull.

All 33 headline series across 11 categories, plus the 119 variant cuts surfaced under each headline as "Also available as...". Each headline entry: `dataset_key` · frequency · unit · verbatim `why_it_matters` (lifted from the canonical catalog).

Featured geography across the catalog is Tampa-St. Petersburg-Clearwater MSA (RegionID 395148), benchmarked against Florida (RegionID 14) + United States (RegionID 102001). Swap `RegionID` in the Python snippet for any metro/state/county/city/ZIP/neighborhood RegionID — Zillow's CSVs ship every level a given series supports in the same file.

For a richer shape (variant URLs, tags, geo levels, full python_snippet per series), consult `references/zillow-datasets.yaml` alongside this file.

## Table of contents

- [Home Values & Forecast](#home-values--forecast) — 2 headlines + 11 variants
- [Mortgage & Carry Cost](#mortgage--carry-cost) — 2 headlines + 4 variants
- [Rents (Level, Demand, Forecast)](#rents-level-demand-forecast) — 3 headlines + 9 variants
- [Inventory & Listings Flow](#inventory--listings-flow) — 3 headlines + 13 variants
- [Prices & Sales](#prices--sales) — 5 headlines + 21 variants
- [Negotiation & Pricing Power](#negotiation--pricing-power) — 2 headlines + 14 variants
- [Velocity (Days on Market)](#velocity-days-on-market) — 2 headlines + 14 variants
- [Price Cuts](#price-cuts) — 3 headlines + 33 variants
- [Market Heat (Composite)](#market-heat-composite) — 1 headline
- [New Construction](#new-construction) — 4 headlines
- [Affordability](#affordability) — 6 headlines

## Home Values & Forecast

- **zillow_zhvi** · monthly · dollars

  Zillow's flagship home-value series — the "typical home value" number you can actually defend in a conversation. Smoothed and seasonally adjusted across SFR + condo stock, so month-over-month moves aren't just noise.

  *Also available as (10 variants):*
  - ZHVI All Homes (SFR, Condo/Co-op) Time Series, Raw, Mid-Tier ($)
  - ZHVI All Homes- Top Tier Time Series ($)
  - ZHVI All Homes- Bottom Tier Time Series ($)
  - ZHVI Single-Family Homes Time Series ($)
  - ZHVI Condo/Co-op Time Series ($)
  - ZHVI 1-Bedroom Time Series ($)
  - ZHVI 2-Bedroom Time Series ($)
  - ZHVI 3-Bedroom Time Series ($)
  - ZHVI 4-Bedroom Time Series ($)
  - ZHVI 5+ Bedroom Time Series ($)

- **zillow_zhvf** · monthly · percent

  Zillow's month/quarter/year-ahead forecast of ZHVI growth, built on the neural Zestimate. Treat as a directional prior for metro-level appreciation — not a number to underwrite a deal on, but honest about which way the wind's blowing.

  *Also available as (1 variant):*
  - ZHVF (Forecast), All Homes (SFR, Condo/Co-op), Raw, Mid-Tier (MoM%, QoQ%, YoY%)

## Mortgage & Carry Cost

- **zillow_mortgage_payment** · monthly · dollars

  Zillow's estimate of monthly principal + interest at the current month's average rate and the typical ZHVI home value. Three down-payment variants (5/10/20%) let you model a buyer's sticker shock without rebuilding the math yourself.

  *Also available as (2 variants):*
  - Mortgage Payment: 10% down, All Homes, Smoothed & Seasonally Adjusted Time Series
  - Mortgage Payment: 5% down, All Homes, Smoothed & Seasonally Adjusted Time Series

- **zillow_total_monthly_payment** · monthly · dollars

  P&I plus property tax, insurance, and a 0.5%-of-value maintenance line — the actual monthly carry on a typical home at today's rates. Closer to real cashflow math than the raw mortgage number.

  *Also available as (2 variants):*
  - Total Monthly Payment: 10% down, All Homes, Smoothed & Seasonally Adjusted Time Series
  - Total Monthly Payment: 5% down, All Homes, Smoothed & Seasonally Adjusted Time Series

## Rents (Level, Demand, Forecast)

- **zillow_zori** · monthly · dollars

  Rent's answer to ZHVI — a repeat-rent index weighted to the actual rental stock. Pair with ZHVI to read gross yield across a metro in two lines of pandas instead of scraping listings.

  *Also available as (5 variants):*
  - ZORI (Smoothed, Seasonally Adjusted): All Homes Plus Multifamily Time Series ($)
  - ZORI (Smoothed): Single Family Residence Time Series ($)
  - ZORI (Smoothed, Seasonally Adjusted): Single Family Residence Time Series ($)
  - ZORI (Smoothed): Multi Family Residence Time Series ($)
  - ZORI (Smoothed, Seasonally Adjusted): Multi Family Residence Time Series ($)

- **zillow_zordi** · monthly · index

  Tracks renter engagement on Zillow listings to proxy demand, smoothed to strip volatility. Leading indicator for rent moves — ZORDI climbs first, then ZORI follows.

  *Also available as (3 variants):*
  - ZORDI: Single Family Residence Time Series
  - ZORDI: Condo/Co-op Time Series
  - ZORDI: Multifamily Residence Time Series

- **zillow_zorf** · monthly · percent

  Month/quarter/year-ahead forecast for ZORI rent growth, SFR and multifamily cuts published separately. National-only — for metro calls, pair ZORI's trailing trend with your own top-down.

  *Also available as (1 variant):*
  - ZORF, (Multi Family Residence, Smoothed)

## Inventory & Listings Flow

- **zillow_for_sale_inventory** · monthly · count

  Unique active listings at the metro level, month by month. Rising inventory is where buyers start to regain leverage; falling inventory is where you end up competing with cash.

  *Also available as (7 variants):*
  - For-Sale Inventory (Smooth, All Homes, Weekly)
  - For-Sale Inventory (Smooth, SFR Only, Monthly)
  - For-Sale Inventory (Smooth, SFR Only, Weekly)
  - For-Sale Inventory (Raw, All Homes, Monthly)
  - For-Sale Inventory (Raw, All Homes, Weekly)
  - For-Sale Inventory (Raw, SFR Only, Monthly)
  - For-Sale Inventory (Raw, SFR Only, Weekly)

- **zillow_new_listings** · monthly · count

  How much fresh supply hit the market this month. Contrast with For-Sale Inventory to separate "supply growing because nothing sells" from "supply growing because sellers are listing."

  *Also available as (3 variants):*
  - New Listings (Smooth, All Homes, Weekly)
  - New Listings (Raw, All Homes, Monthly)
  - New Listings (Raw, All Homes, Weekly)

- **zillow_newly_pending_listings** · monthly · count

  Listings that went under contract this month. The demand counterpart to new listings — pair the two to see whether the market is absorbing supply or choking on it.

  *Also available as (3 variants):*
  - Newly Pending Listings (Raw, All Homes, Weekly)
  - Newly Pending Listings (Smoothed, All Homes, Monthly)
  - Newly Pending Listings (Smoothed, All Homes, Weekly)

## Prices & Sales

- **zillow_median_list_price** · monthly · dollars

  Median asking price of active listings — the seller's opening bid. Useful alongside Median Sale Price and the Sale-to-List Ratio to read how much sellers are getting shaved on the way to close.

  *Also available as (7 variants):*
  - Median List Price (Smooth, All Homes, Weekly)
  - Median List Price (Smooth, SFR Only, Monthly)
  - Median List Price (Smooth, SFR Only, Weekly)
  - Median List Price (Raw, All Homes, Monthly)
  - Median List Price (Raw, All Homes, Weekly)
  - Median List Price (Raw, SFR Only, Monthly)
  - Median List Price (Raw, SFR Only, Weekly)

- **zillow_sales_count** · monthly · count

  Transaction volume per month. Nowcast cut blends recent on-market and off-market data — use it to gut-check whether a price move is happening on real volume or just on a handful of deals.

  *Also available as (3 variants):*
  - Sales Count (Raw, SFR only, Monthly)
  - Sales Count (Smooth, All Homes, Weekly)
  - Sales Count (Smooth, SFR only, Weekly)

- **zillow_median_sale_price** · monthly · dollars

  What the middle home actually traded at. Noisier than ZHVI because the mix of what sold shifts month to month — always read it alongside ZHVI, never in isolation.

  *Also available as (3 variants):*
  - Median Sale Price (Raw, SFR only, Monthly)
  - Median Sale Price (Smooth, All Homes, Weekly)
  - Median Sale Price (Smooth, SFR only, Weekly)

- **zillow_mean_sale_price** · monthly · dollars

  Average sale price — dragged around by a few big trades each month. Gap vs. median sale price shows how top-heavy the local sales distribution is that month.

  *Also available as (5 variants):*
  - Mean Sale Price (Smooth & Seasonally Adjusted, SFR only, Monthly)
  - Mean Sale Price (Raw, SFR only, Monthly)
  - Mean Sale Price (Smooth & Seasonally Adjusted, SFR only, Weekly)
  - Mean Sale Price (Smooth, All Homes, Weekly)
  - Mean Sale Price (Smooth, SFR only, Weekly)

- **zillow_total_transaction_value** · monthly · dollars

  Dollar volume of all sales per month. Sales count × mean sale price, basically — handy for sizing a market or comparing a metro's flow vs. another's in raw capital-deployed terms.

  *Also available as (3 variants):*
  - Total Transaction Value (Raw, SFR only, Monthly)
  - Total Transaction Value (Smooth, All Homes, Weekly)
  - Total Transaction Value (Smooth, SFR only, Weekly)

## Negotiation & Pricing Power

- **zillow_sale_to_list_ratio** · monthly · ratio

  Average ratio of sale price to the last list price. Above 1.0 = bidding wars; well below 1.0 = price cuts landing. One of the cleanest reads of seller vs. buyer leverage in a market.

  *Also available as (7 variants):*
  - Mean Sale-to-List Ratio (Smooth, All Homes, Monthly)
  - Mean Sale-to-List Ratio (Raw, All Homes, Weekly)
  - Mean Sale-to-List Ratio (Smooth, All Homes, Weekly)
  - Median Sale-to-List Ratio (Raw, All Homes, Monthly)
  - Median Sale-to-List Ratio (Smooth, All Homes, Monthly)
  - Median Sale-to-List Ratio (Raw, All Homes, Weekly)
  - Median Sale-to-List Ratio (Smooth, All Homes, Weekly)

- **zillow_share_sold_above_below_list** · monthly · percent

  What fraction of sales went over or under the last list price. Inverse pair — when the Above-List share rises, Below-List falls — but the numbers don't have to sum to 100% because of exact-list sales.

  *Also available as (7 variants):*
  - Percent of Homes Sold Above List (Smooth, All Homes, Monthly)
  - Percent of Homes Sold Above List (Raw, All Homes, Weekly)
  - Percent of Homes Sold Above List (Smooth, All Homes, Weekly)
  - Percent of Homes Sold Below List (Raw, All Homes, Monthly)
  - Percent of Homes Sold Below List (Smooth, All Homes, Monthly)
  - Percent of Homes Sold Below List (Raw, All Homes, Weekly)
  - Percent of Homes Sold Below List (Smooth, All Homes, Weekly)

## Velocity (Days on Market)

- **zillow_days_to_pending** · monthly · days

  Days from list to pending contract — the velocity counterpart to inventory. If listings still go pending in under a week, the market hasn't actually cooled no matter what prices say.

  *Also available as (7 variants):*
  - Mean Days to Pending (Smooth, All Homes, Weekly)
  - Mean Days to Pending (Raw, All Homes, Monthly)
  - Mean Days to Pending (Raw, All Homes, Weekly)
  - Median Days to Pending (Smooth, All Homes, Monthly)
  - Median Days to Pending (Smooth, All Homes, Weekly)
  - Median Days to Pending (Raw, All Homes, Monthly)
  - Median Days to Pending (Raw, All Homes, Weekly)

- **zillow_days_to_close** · monthly · days

  Days from contract to close — a read on the transaction machinery (inspections, financing, title). Climbs when appraisal delays or rate-lock churn stretch timelines; compresses in clean cash markets.

  *Also available as (7 variants):*
  - Mean Days to Close (Smooth, All Homes, Monthly)
  - Mean Days to Close (Raw, All Homes, Weekly)
  - Mean Days to Close (Smooth, All Homes, Weekly)
  - Median Days to Close (Raw, All Homes, Monthly)
  - Median Days to Close (Smooth, All Homes, Monthly)
  - Median Days to Close (Raw, All Homes, Weekly)
  - Median Days to Close (Smooth, All Homes, Weekly)

## Price Cuts

- **zillow_share_price_cut** · monthly · percent

  What share of active listings have dropped their ask. Early warning for a cooling market — sellers cut price before they cut contracts, and this moves before sale-to-list ratios do.

  *Also available as (7 variants):*
  - Share of Listings With a Price Cut (Smooth, All Homes, Weekly)
  - Share of Listings With a Price Cut (Raw, All Homes, Monthly)
  - Share of Listings With a Price Cut (Raw, All Homes, Weekly)
  - Share of Listings With a Price Cut (Smooth, SFR Only, Monthly)
  - Share of Listings With a Price Cut (Smooth, SFR Only, Weekly)
  - Share of Listings With a Price Cut (Raw, SFR Only, Monthly)
  - Share of Listings With a Price Cut (Raw, SFR Only, Weekly)

- **zillow_price_cut_dollars** · monthly · dollars

  Typical dollar size of the markdown when a listing cuts price. Rising cut amount alongside rising cut share says sellers are chasing the market down aggressively.

  *Also available as (15 variants):*
  - Mean Price Cut ($, Raw, SFR Only, Weekly)
  - Mean Price Cut ($, Smoothed, SFR Only, Monthly)
  - Mean Price Cut ($, Smoothed, SFR Only, Weekly)
  - Mean Price Cut ($, Raw, All Homes, Monthly)
  - Mean Price Cut ($, Raw, All Homes, Weekly)
  - Mean Price Cut ($, Smoothed, All Homes, Monthly)
  - Mean Price Cut ($, Smoothed, All Homes, Weekly)
  - Median Price Cut ($, Raw, SFR Only, Monthly)
  - Median Price Cut ($, Raw, SFR Only, Weekly)
  - Median Price Cut ($, Smoothed, SFR Only, Monthly)
  - Median Price Cut ($, Smoothed, SFR Only, Weekly)
  - Median Price Cut ($, Raw, All Homes, Monthly)
  - Median Price Cut ($, Raw, All Homes, Weekly)
  - Median Price Cut ($, Smoothed, All Homes, Monthly)
  - Median Price Cut ($, Smoothed, All Homes, Weekly)

- **zillow_price_cut_percent** · monthly · percent

  Price cut expressed as a percent of the last list price — normalizes across price bands. A 3% cut in a $200K market and a 3% cut in a $2M market tell the same story; dollar cuts don't.

  *Also available as (11 variants):*
  - Mean Price Cut (%, Raw, All Homes, Weeky)
  - Mean Price Cut (%, Smoothed, All Homes, Monthly)
  - Mean Price Cut (%, Smoothed, All Homes, Weekly)
  - Median Price Cut (%, Raw, SFR Only, Monthly)
  - Median Price Cut (%, Raw, SFR Only, Weekly)
  - Median Price Cut (%, Smoothed, SFR Only, Monthly)
  - Median Price Cut (%, Smoothed, SFR Only, Weekly)
  - Median Price Cut (%, Raw, All Homes, Monthly)
  - Median Price Cut (%, Raw, All Homes, Weekly)
  - Median Price Cut (%, Smoothed, All Homes, Monthly)
  - Median Price Cut (%, Smoothed, All Homes, Weekly)

## Market Heat (Composite)

- **zillow_market_heat_index** · monthly · index

  Zillow's composite of supply + demand + price signals, scored so metros land in Buyers / Balanced / Sellers regions. One number to sanity-check what a stack of individual series is telling you.

## New Construction

- **zillow_new_construction_sales_count** · monthly · count

  How many newly-built homes traded this month. Climbs when builders are moving standing inventory; tells you whether local price softness is resale-driven or new-construction-driven.

- **zillow_new_construction_median_sale_price** · monthly · dollars

  Median closing price on new construction. Gap vs. resale median sale price shows the premium (or discount, lately) builders are pricing at — and where builder concessions show up before they hit the headline number.

- **zillow_new_construction_median_price_per_sqft** · monthly · dollars

  Price-per-square-foot on new construction. Size-normalized, so it's less contaminated by builders shifting product mix toward smaller homes to hit affordability targets than the headline median is.

- **zillow_new_construction_mean_sale_price** · monthly · dollars

  Average new-construction sale price. Sensitive to builders pushing a single big community; pair with median to see whether the distribution is bunched or spread.

## Affordability

- **zillow_new_homeowner_income_needed** · monthly · dollars

  Annual income needed to keep the Total Monthly Payment under 30% of gross — the threshold Zillow uses to call a home "affordable." Compare to local median income to see how far underwater typical buyers are.

- **zillow_new_renter_income_needed** · monthly · dollars

  Annual income needed to keep typical rent under 30% of gross. Pair with the homeowner equivalent to see how the affordability gap between renting and buying is moving in a metro.

- **zillow_affordable_home_price** · monthly · dollars

  What a buyer at local median income could afford to spend, working backwards from the 30%-of-gross-income rule at current rates. Gap vs. ZHVI is the affordability gap in dollar terms.

- **zillow_years_to_save** · monthly · years

  How long a typical renter would need to save for a 20% down payment on a typically-priced home. Climbs when prices outrun incomes; cools when savings yields finally pay.

- **zillow_new_homeowner_affordability** · monthly · percent

  Share of a median-income household's gross that goes to Total Monthly Payment on a typical home. Above 30% = Zillow's affordability threshold breached; watch the trend, not just the level.

- **zillow_new_renter_affordability** · monthly · percent

  Share of a median-income renter's gross consumed by typical rent. The renter's version of Zillow's 30%-of-income threshold — trend matters more than any single month's read.
