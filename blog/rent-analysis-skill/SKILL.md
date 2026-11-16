---
name: rent-analysis
description: Compare county rents in any US state using Zillow's ZORI file. Use when asked how rents in a county are moving, how two counties compare, or whether to raise or hold rent. Runs rent_report.py, then explains what the index measures and what it can't tell you.
---
# Reading county rent data
Run `python rent_report.py STATE "County" ["County" ...]` from this folder (needs pandas). Quote only numbers from its JSON, never your own math, and name the `as_of` month.
## What the index measures
ZORI is Zillow's smoothed index of asking rents on listed homes and apartments. It is not what sitting tenants pay.
## How to compare
- Compare `yoy_pct`, not dollars. County rent levels differ for reasons unrelated to momentum.
- Read `yoy_pct` next to `vs_peak_pct` and `peak_month`: a county can be up on the year and still below its peak.
- Use `state_median_yoy_pct` and `yoy_rank` for context. Within a point of the median is "in line", not a story.
## What to say it can't tell
It can't tell your tenant's rent, your unit's rent, bedroom or neighborhood differences, vacancy, or why rents moved. Label any cause as a guess. If a county is in `not_found`, say so; don't substitute a neighbor.
End with one practical step: check comps near your property before changing a lease.
