# Realtor Real-Estate Metrics — Full Reference

Load this file when a user asks about a specific Realtor column, when a decision playbook in the parent `SKILL.md` points here, or when you need the `csv_column` to pull.

All 14 columns across 5 groupings, sourced from Realtor.com Research's Monthly Housing Inventory feed. Each entry: `key` · `csv_column` · frequency · unit · verbatim rationale (lifted from the canonical catalog).

Geography default is Hillsborough County, FL (FIPS `12057`), with Florida (state_id `FL`) + United States (country `USA`) benchmarks per dataset. Swap the CSV URL stem (`_County_` → `_State_` / `_Country_`) and the filter column (`county_fips` int → `state_id` string → no filter) for the geography you need.

For a richer shape (CSV URLs, YoY column names, benchmark geographies, copy-pasteable Python snippets), consult `references/realtor-datasets.yaml` alongside this file.

## Table of contents

- [Prices](#prices) — 3 columns
- [Supply](#supply) — 3 columns
- [Demand & Velocity](#demand--velocity) — 3 columns
- [Pricing Action](#pricing-action) — 4 columns
- [Mix](#mix) — 1 column

## Prices

- **realtor_median_listing_price** · `median_listing_price` · monthly · dollars

  The headline number every Hillsborough offer negotiates against. Compare Tampa's trajectory against Florida and the U.S. to see whether you're paying a premium to the state or buying at a discount to the national mean.

- **realtor_median_listing_price_per_square_foot** · `median_listing_price_per_square_foot` · monthly · dollars

  Price normalized by size — the one Tampa-vs-elsewhere comparison that controls for house-size differences. When the Hillsborough line diverges from the FL or U.S. benchmark, you're seeing a real valuation gap, not just a size mix shift.

- **realtor_average_listing_price** · `average_listing_price` · monthly · dollars

  The arithmetic mean listing price — sensitive to high-end outliers in a way the median isn't. Paired with the median, a widening gap (average running well above median) means the luxury tail is pulling the market up; compression means the mid-market is carrying the action.

## Supply

- **realtor_active_listing_count** · `active_listing_count` · monthly · count

  Live for-sale inventory in Hillsborough. Climbing faster than Florida or the U.S. means local supply is loosening ahead of the cycle — bid with more room; lagging the benchmarks means tight market, offer accordingly.

- **realtor_new_listing_count** · `new_listing_count` · monthly · count

  Fresh supply hitting the Tampa market each month. Accelerating above Florida or the U.S. means sellers are testing the market faster here — watch it with active_listing_count to separate "supply is growing" from "listings are churning without selling."

- **realtor_total_listing_count** · `total_listing_count` · monthly · count

  Everything the MLS sees in Hillsborough — active plus pending. The wider supply gauge compared to active_listing_count; use the two together to separate "supply is real" (both up) from "supply is just churn" (total flat, active up).

## Demand & Velocity

- **realtor_median_days_on_market** · `median_days_on_market` · monthly · days

  How long the median Hillsborough listing sits before going under contract. Stretching faster than Florida or the U.S. means demand is cooling locally ahead of the benchmark — shorter means you're bidding into a tighter competitive market than average.

- **realtor_pending_listing_count** · `pending_listing_count` · monthly · count

  Hillsborough listings under contract but not yet closed — the near-term demand gauge. Stronger growth than Florida or the U.S. signals pending deal volume running hot locally; leading indicator of closed-sale momentum 30-60 days out.

- **realtor_pending_ratio** · `pending_ratio` · monthly · ratio

  Pending listings divided by active — a direct demand-vs-supply tightness gauge. Above 1.0 means deals in motion outnumber homes still for sale (hot); below means a supply overhang. Comparing Hillsborough's ratio to Florida and the U.S. tells you whether Tampa is running hotter or cooler than the surrounding baseline.

## Pricing Action

- **realtor_price_increased_count** · `price_increased_count` · monthly · count

  Count of Hillsborough listings where a seller raised their asking price in the month. A rising line vs. Florida or the U.S. is the early read on seller confidence pushing back against cooling demand — read paired with price-reduced counts for the full tone.

- **realtor_price_increased_share** · `price_increased_share` · monthly · percent

  Normalized version of the raw count — what fraction of active Hillsborough listings raised their price this month. Less noisy than the count when inventory swings; the benchmark lines tell you whether seller confidence is local or sector-wide.

- **realtor_price_reduced_count** · `price_reduced_count` · monthly · count

  Count of Hillsborough listings where the seller cut their asking price in the month. The cleanest read on where negotiating leverage is shifting — above the FL or U.S. trendline means Tampa sellers are blinking first.

- **realtor_price_reduced_share** · `price_reduced_share` · monthly · percent

  Fraction of active Hillsborough listings that saw a price cut this month. The share-form is the one to watch for cycle turns — when Tampa's line runs above Florida's and the U.S., buyers have disproportionate leverage here.

## Mix

- **realtor_median_square_feet** · `median_square_feet` · monthly · count

  The typical Hillsborough listing's size. Shifting faster than the Florida or U.S. median tells you the inventory mix is changing — smaller homes going on the market (entry-level supply loosening) or larger ones (move-up inventory expanding).
