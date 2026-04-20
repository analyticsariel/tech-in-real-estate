# HMDA Real Estate

A Claude skill that maps the **14 CFPB HMDA Data Browser aggregation metrics** a residential investor actually uses — originations, applications, denial rate, purchase-vs-refi mix, cash-out share, FHA/VA/conventional product mix, loan volume, average purchase loan, small-multi and manufactured financeability, plus a single fair-lending read — grouped into **6 categories** (credit access, loan purpose cycle, product mix, volume & size, property type, fair lending) and threaded through **decision playbooks** — so "is credit tightening in Hillsborough?" or "where is the mortgage cycle right now?" becomes a one-line ask, not a re-paste of the CFPB action-taken code list.

## What it does

The CFPB HMDA Data Browser exposes a public JSON aggregations endpoint that returns `{count, sum}` buckets per geography and year across every US mortgage filing above the HMDA threshold. For US residential real estate, 14 of those aggregation cuts carry the credit-access, cycle, mix, volume, property-type, and fair-lending read every local investor needs. This skill teaches Claude which 14 metrics matter, the exact query-string filters per metric, the derivation type (count, denial-rate, share, sum-dollars, avg-loan-amount, subgroup-denial-rate), and how to read each metric against Florida + US benchmarks rather than in isolation. Decision playbooks thread them into the questions an investor actually asks — credit loosening, cycle position, marginal-buyer product mix, capital flow, non-SFR financing, fair-lending convergence.

Progressive disclosure: the skill loads the 6-category table up front, then pulls the full 14-metric reference or the canonical YAML only when the question demands it.

## Install

```bash
cp -r skills/hmda-real-estate ~/.claude/skills/
```

Then restart Claude Code. The skill auto-triggers when the question mentions HMDA, Home Mortgage Disclosure Act, CFPB data, mortgage originations, denial rate, refi count, FHA / VA / conventional share, loan volume, fair lending, credit access, or Hillsborough County / Tampa mortgage market — no explicit invocation needed.

Prereq: none. CFPB HMDA Data Browser aggregations are public — no API key, no login.

## What's here

```
hmda-real-estate/
  SKILL.md                              # Claude-facing frontmatter + body
  README.md                             # this file
  references/
    metrics.md                          # full 14-metric reference — key, api_endpoint, frequency, unit, verbatim rationale
    hmda-datasets.yaml                  # canonical YAML catalog — API URLs, benchmark geographies, Python snippets, fetcher notes
```

`SKILL.md` carries the pushy description that controls when Claude loads the skill, plus the 6-category table, decision playbooks, a minimal `requests`-based snippet against the aggregations endpoint, and the gotchas (geo filter required, 2-criteria max, six silently no-op filters, two-letter state `code`, annual cadence with summer lag, no median on aggregations, `servedFrom` caching semantics, Sprint 14 MSA-to-county swap).

`references/metrics.md` is the one-page reference with every HMDA metric, its `api_endpoint` template, and the investor rationale verbatim from the catalog. Load it when a specific metric or filter combination is needed.

`references/hmda-datasets.yaml` is the canonical catalog — the same shape TiRE uses internally, with 100% field coverage (API endpoint, derivation notes, Hillsborough × Florida × USA benchmark configuration, Python snippet per metric, fetcher action/loan-purpose/loan-type code reference).

## Source of truth

This skill is **mirrored** from `analyticsariel/tech-in-real-estate-ops` (private). The canonical HMDA dataset catalog lives there at `agents/data/hmda-datasets.yaml` and is the upstream of the YAML shipped here. If the private catalog changes, the mirror regenerates.

Live detail page on the TiRE site: <https://techinrealestate.com/skills/hmda-real-estate>.

## License

MIT. Use, fork, adapt — credit TiRE if it helps you, and file issues in this repo if you find rough edges.
