# FRED Real Estate

A Claude skill that maps the **44 FRED series** a leveraged residential investor actually uses, grouped into **9 categories** and threaded through **6 decision playbooks** — so "is now a good time to buy?" or "how's the rental market?" becomes a one-line ask, not a re-paste of the FRED API docs.

## What it does

FRED publishes ~800,000 economic time series. For US residential real estate, 44 of them do the real analytical work — mortgage rates, home-price indices, affordability, supply (permits → starts → completions → active listings), demand, rent inflation, homeownership tenure, employment, real income, inflation, and credit stress. This skill teaches Claude which series those are, which `series_id` to pull for each, how to read them (seasonal adjustment, release lag, SAAR), and six playbooks that thread them into the decisions an investor actually makes.

Progressive disclosure: the skill loads a category table up front, then pulls the full 44-series reference or the canonical YAML only when the question demands it.

## Install

```bash
cp -r skills/fred-real-estate ~/.claude/skills/
```

Then restart Claude Code. The skill auto-triggers when the question mentions mortgage rates, affordability, supply, prices, rent inflation, employment, or credit stress — no explicit invocation needed.

Prereq: a free FRED API key from <https://fred.stlouisfed.org/docs/api/api_key.html>, set as `FRED_API_KEY` in your environment. Rate limit is 120 req/min (not a concern for personal use).

## What's here

```
fred-real-estate/
  SKILL.md                      # Claude-facing frontmatter + body
  README.md                     # this file
  references/
    metrics.md                  # full 44-series reference — series_id, frequency, unit, one-line rationale
    references/fred-series.yaml # canonical YAML catalog — tags, publisher, FRED URL, data-quality notes
```

`SKILL.md` carries the pushy description that controls when Claude loads the skill, plus the 9-category table, 6 decision playbooks, a minimal `fredapi` snippet, and the gotchas (SA vs. NSA, SAAR, release lag, `FIXHAI` limits).

`references/metrics.md` is the one-page reference with every `series_id` and its rationale. Load it when a specific metric or the full list is needed.

`references/fred-series.yaml` is the canonical catalog — the same shape TiRE uses internally, with 100% field coverage (tags, source publisher, FRED landing URL, data-quality notes).

## Source of truth

This skill is **mirrored** from `analyticsariel/tech-in-real-estate-ops` (private). The canonical FRED series catalog lives there at `agents/data/fred-series.yaml` and is the upstream of the YAML shipped here. If the private catalog changes, the mirror regenerates.

Live detail page on the TiRE site: <https://techinrealestate.com/skills/fred-real-estate>.

## License

MIT. Use, fork, adapt — credit TiRE if it helps you, and file issues in this repo if you find rough edges.
