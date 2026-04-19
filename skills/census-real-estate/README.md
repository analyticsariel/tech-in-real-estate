# Census Real Estate

A Claude skill that maps the **12 ACS 5-Year datasets** a residential investor actually uses — demographics, household income, rent, home value, tenure, vacancy, stock — grouped into **5 categories** and threaded through **6 decision playbooks** — so "can renters here afford a $2,000/mo unit?" or "is this market priced to local income or imported demand?" becomes a one-line ask, not a re-paste of the Census API docs.

## What it does

The U.S. Census Bureau publishes thousands of ACS variables. For US residential real estate, 12 of them carry most of the submarket thesis — population growth, bachelor's-share, LFPR, median household income, median gross rent, median owner costs, rent burden, median home value, homeownership rate, vacancy rate, housing units, median year built. This skill teaches Claude which variables those are, which ACS table and variable ID to pull for each, the derivation when a metric is a ratio over raw variables, how to read them (5-year pooling, release lag, inflation-adjustment to vintage end-year), and six playbooks that thread them into the decisions an investor actually makes.

Progressive disclosure: the skill loads a category table up front, then pulls the full 12-dataset reference or the canonical YAML only when the question demands it.

## Install

```bash
cp -r skills/census-real-estate ~/.claude/skills/
```

Then restart Claude Code. The skill auto-triggers when the question mentions ACS, Census, B25/B19013 tables, median income, rent, home value, rent burden, homeownership, vacancy, housing units, or tract-level demand — no explicit invocation needed.

Prereq: a free Census API key from <https://api.census.gov/data/key_signup.html>, set as `CENSUS_API_KEY` in your environment. Without a key the Census API caps at 500 requests/day per IP; with a key it's effectively unlimited.

## What's here

```
census-real-estate/
  SKILL.md                         # Claude-facing frontmatter + body
  README.md                        # this file
  references/
    metrics.md                     # full 12-dataset reference — dataset_key, ACS variable IDs, frequency, unit, verbatim rationale
    references/census-datasets.yaml  # canonical YAML catalog — ACS table IDs, variable names, derivation blocks, benchmark geographies, notes
```

`SKILL.md` carries the pushy description that controls when Claude loads the skill, plus the 5-category table, 6 decision playbooks, a minimal `requests`-based snippet against the ACS 5-Year API, and the gotchas (5-year pooling, release lag, self-reported home values, MOE at sub-county grain, gross vs contract rent, derivation blocks).

`references/metrics.md` is the one-page reference with every `dataset_key`, its ACS variable IDs, and the investor rationale verbatim from the catalog. Load it when a specific dataset or variable is needed.

`references/census-datasets.yaml` is the canonical catalog — the same shape TiRE uses internally, with 100% field coverage (ACS table IDs, derivation formulas, Hillsborough × Florida × USA benchmark configuration, notes).

## Source of truth

This skill is **mirrored** from `analyticsariel/tech-in-real-estate-ops` (private). The canonical Census dataset catalog lives there at `agents/data/census-datasets.yaml` and is the upstream of the YAML shipped here. If the private catalog changes, the mirror regenerates.

Live detail page on the TiRE site: <https://techinrealestate.com/skills/census-real-estate>.

## License

MIT. Use, fork, adapt — credit TiRE if it helps you, and file issues in this repo if you find rough edges.
