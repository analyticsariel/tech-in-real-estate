# FEMA Real Estate

A Claude skill that maps the **12 OpenFEMA v2 metrics** a residential investor actually uses to read climate-and-insurance exposure at the county level — disaster declarations, hurricane-only declarations, NFIP flood-insurance claim count / paid dollars / average severity / gross building damage, Individual Assistance grants total and split owner-vs-renter, disaster registrations count, Public Assistance federal obligation, and permanent-work share — grouped into **4 categories** (disaster frequency, flood insurance, individual assistance, public assistance) and threaded through **decision playbooks** — so "how disaster-exposed is Hillsborough?" or "is the insurance market under-paying damage claims?" becomes a one-line ask, not a re-paste of OpenFEMA's per-dataset filter quirks.

## What it does

OpenFEMA v2 ships 5 event-row datasets that, together, describe the federal-disaster footprint on any US county: `DisasterDeclarationsSummaries` (one row per disaster × county designation), `FimaNfipClaims` (one row per flood-insurance claim), `PublicAssistanceFundedProjectsDetails` (one row per PA-funded infrastructure project), `HousingAssistanceOwners` + `HousingAssistanceRenters` (disaster × zip rollups of IA grants to owners / renters), and `RegistrationIntakeIndividualsHouseholdPrograms` (pre-aggregated IHP roll-ups). For US residential real estate, 12 aggregations of these datasets carry the disaster-frequency, flood-insurance-cost, household-assistance, and federal-rebuild read every county investor needs. This skill teaches Claude which 12 metrics matter, the exact `$filter` template per metric, the per-dataset county-code encoding (5 distinct forms — yes, really), how to join date-less datasets against DDS for year attribution, and how to read each metric against Florida + US benchmarks rather than in isolation. Decision playbooks thread them into the questions an investor actually asks — how often FEMA shows up, whether insurance is actually settling claims, who gets federal checks when a storm hits, whether the rebuild is real.

Progressive disclosure: the skill loads the 4-category table up front, then pulls the full 12-metric reference or the canonical YAML only when the question demands it.

## Install

```bash
cp -r skills/fema-real-estate ~/.claude/skills/
```

Then restart Claude Code. The skill auto-triggers when the question mentions FEMA, OpenFEMA, disaster declarations, hurricane declarations, NFIP, flood claims, flood insurance, NFIP payouts, IHP, Individuals and Households Program, disaster assistance, owner IA, renter IA, disaster registrations, Public Assistance, PA federal obligation, permanent work share, Hillsborough County, or Tampa flood / hurricane exposure — no explicit invocation needed.

Prereq: none. OpenFEMA v2 is public — no API key, no login.

## What's here

```
fema-real-estate/
  SKILL.md                              # Claude-facing frontmatter + body
  README.md                             # this file
  references/
    metrics.md                          # full 12-metric reference — key, OpenFEMA dataset, $filter template, frequency, unit, verbatim rationale
    fema-datasets.yaml                  # canonical YAML catalog — API URLs, benchmark geographies, Python snippets, fetcher notes on per-dataset county encoding
```

`SKILL.md` carries the pushy description that controls when Claude loads the skill, plus the 4-category table, 6 decision playbooks, a minimal `requests`-based snippet against `DisasterDeclarationsSummaries`, and 10 gotchas (5-form county-encoding matrix, state field name drift, national = absence of state + county filter, DDS year-join for date-less datasets, RegIntake vs row-per-registration swap, explicit deferrals of `FimaNfipPolicies` + `HazardMitigationAssistance*`, null handling, hurricane zero-years, 2010–2024 window, keyless-but-polite).

`references/metrics.md` is the one-page reference with every FEMA metric, its OpenFEMA dataset + `$filter` template, and the investor rationale verbatim from the catalog. Load it when a specific metric or filter combination is needed.

`references/fema-datasets.yaml` is the canonical catalog — the same shape TiRE uses internally, with 100% field coverage (API endpoint, per-dataset county + state filter fields, Hillsborough × Florida × USA benchmark configuration, Python snippet per metric, fetcher derivation notes).

## Source of truth

This skill is **mirrored** from `analyticsariel/tech-in-real-estate-ops` (private). The canonical FEMA dataset catalog lives there at `agents/data/fema-datasets.yaml` and is the upstream of the YAML shipped here. If the private catalog changes, the mirror regenerates.

Live detail page on the TiRE site: <https://techinrealestate.com/skills/fema-real-estate>.

## License

MIT. Use, fork, adapt — credit TiRE if it helps you, and file issues in this repo if you find rough edges.
