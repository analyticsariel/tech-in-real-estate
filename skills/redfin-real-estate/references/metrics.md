# Redfin Real-Estate Metrics — Full Reference

Load this file when a user asks about a specific Redfin metric, when a decision playbook in the parent `SKILL.md` points here, or when you need the `csv_column` to pull.

All 14 metrics across 5 categories. Each entry: `dataset_key` · `csv_column` · frequency · unit · verbatim rationale (lifted from the canonical catalog).

Geography default is Hillsborough County, FL (TABLE_ID 464), with Florida (STATE_CODE "FL") + United States benchmarks per metric. Substitute `state_market_tracker` or `us_national_market_tracker` in the TSV stem for the FL or US benchmark file. All entries pull from Redfin's Monthly Market Tracker dataset; filter `PROPERTY_TYPE_ID = -1` (All Residential) and `IS_SEASONALLY_ADJUSTED = False` on every read.

For a richer shape (TSV URLs, Python snippets, benchmark config, fetcher notes), consult `references/redfin-datasets.yaml` alongside this file.

## Table of contents

- [Prices](#prices) — 4 metrics
- [Sales & Demand](#sales--demand) — 2 metrics
- [Inventory & Supply](#inventory--supply) — 3 metrics
- [Velocity](#velocity) — 2 metrics
- [Negotiation](#negotiation) — 3 metrics

## Prices

- **redfin_median_sale_price** · `MEDIAN_SALE_PRICE` · monthly · dollars

  What houses actually trade for in Hillsborough — not list, not estimate. Track it against Florida and the U.S. to see whether Tampa is running hot, cooling off, or riding the national tide.

- **redfin_median_list_price** · `MEDIAN_LIST_PRICE` · monthly · dollars

  Where Hillsborough sellers start the conversation. Pair it with median sale price and the list-vs-sale gap tells you how much room there is in the negotiation — a widening gap against Florida or the U.S. means sellers are leaning optimistic relative to the benchmark.

- **redfin_median_ppsf** · `MEDIAN_PPSF` · monthly · dollars

  Price per square foot strips the size mix out of the median. Rising Hillsborough PPSF while Florida stays flat means buyers are paying up for Tampa density, not just bigger houses — different signal, different reaction.

- **redfin_median_list_ppsf** · `MEDIAN_LIST_PPSF` · monthly · dollars

  What Hillsborough sellers ask per square foot, normalized for size. When list PPSF pulls ahead of sale PPSF locally and the gap widens versus Florida or the U.S., expect more price reductions in the next 60 days.

## Sales & Demand

- **redfin_homes_sold** · `HOMES_SOLD` · monthly · count

  Closed deals per month in Hillsborough. When Tampa volume falls faster than Florida or the U.S., local demand is cracking before the macro cycle catches up — that's the window where buyers get leverage.

- **redfin_pending_sales** · `PENDING_SALES` · monthly · count

  Deals under contract but not yet closed. Pending is the forward-looking read on Hillsborough — when Tampa pendings slow versus Florida or the U.S., next month's sale count follows.

## Inventory & Supply

- **redfin_new_listings** · `NEW_LISTINGS` · monthly · count

  Fresh inventory hitting Hillsborough each month. Surging local new listings relative to Florida or the U.S. means Tampa sellers are getting antsy — more negotiating room for buyers, compressed margins for flippers.

- **redfin_inventory** · `INVENTORY` · monthly · count

  What's sitting on the Hillsborough market right now. Rising faster than state or national inventory means Tampa supply is uncorking ahead of the cycle; falling faster means the squeeze is still on and sellers keep the leverage.

- **redfin_months_of_supply** · `MONTHS_OF_SUPPLY` · monthly · ratio

  How many months to clear Hillsborough inventory at current pace. Under four is a seller's market; over six is a buyer's market. Compared against Florida and the U.S., it tells you whether Tampa's tilt is local or part of a broader shift.

## Velocity

- **redfin_median_dom** · `MEDIAN_DOM` · monthly · days

  How long the median Hillsborough listing takes to go pending. When Tampa DOM climbs while Florida and the U.S. stay flat, local demand is thinning first — bidders, not sellers, should notice.

- **redfin_off_market_in_two_weeks** · `OFF_MARKET_IN_TWO_WEEKS` · monthly · percent

  Share of Hillsborough listings that went pending within 14 days. When the local share beats the state and national benchmarks, the A-tier listings are clearing fast — expect bidding pressure on the best stock even in a cooling broader market.

## Negotiation

- **redfin_avg_sale_to_list** · `AVG_SALE_TO_LIST` · monthly · ratio

  Closed price divided by last list price. Above 1.00 means Hillsborough sellers get over ask on average; below 0.97 means real negotiating room. Comparing to Florida and the U.S. shows where Tampa sits on the bargaining spectrum.

- **redfin_sold_above_list** · `SOLD_ABOVE_LIST` · monthly · percent

  Share of Hillsborough closings that finished above asking. When the share runs 10-plus points hotter than Florida or the U.S., you're in a local bidding war — price in a cushion or walk away earlier.

- **redfin_price_drops** · `PRICE_DROPS` · monthly · percent

  Share of active Hillsborough listings that took a price cut in the last week. Higher than Florida or the U.S. means sellers are capitulating faster — buyers can slow-play offers and wait for the cut instead of bidding up.
