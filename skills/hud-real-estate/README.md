# HUD Real Estate

A Claude skill that maps the **12 HUD USER metrics** a residential investor actually uses — Fair Market Rent (2BR + 3BR), Area Median Income (reference + 30/50/80% AMI × 4-person), the MTSP 60% AMI LIHTC rent-cap anchor, and five CHAS cost-burden / priority-pool derivatives — grouped into **3 categories** (rent ceilings, income limits, housing needs) and threaded through **decision playbooks** — so "what's the voucher rent on a 3BR in Tampa?" or "how stretched is the Hillsborough renter pool?" becomes a one-line ask, not a tour of four HUD endpoints and two variable-coding systems.

## What it does

HUD USER exposes a Bearer-token API across four endpoints (FMR, IL, MTSP IL, CHAS) that shape every voucher deal, LIHTC allocation, and affordable-housing program in the country. For US residential real estate, 12 of those cuts carry the rent-ceiling, income-threshold, LIHTC-cap, and cost-burden read every local investor needs. This skill teaches Claude which 12 metrics matter, the exact endpoint and extractor path per metric (including the `A1-J17` CHAS API codes — **different from** the `T{n}_est*` codes in HUD's CSV-download data dictionary), and how to read each metric against Florida + US benchmarks where HUD natively publishes them (FMR none, IL Florida-only, CHAS FL + US). Decision playbooks thread them into the questions an investor actually asks — voucher rent on a 3BR, tenant income eligibility, LIHTC rent caps, renter distress, affordable demand pool, insurance-crisis owner stress.

Progressive disclosure: the skill loads the 3-category table up front, then pulls the full 12-metric reference or the canonical YAML only when the question demands it.

## Install

```bash
cp -r skills/hud-real-estate ~/.claude/skills/
```

Then restart Claude Code. The skill auto-triggers when the question mentions HUD, Fair Market Rent, FMR, Section 8 voucher, Area Median Income, AMI, HAMFI, income limits, 30/50/80% AMI, LIHTC rent caps, MTSP 60% AMI, CHAS, renter cost burden, owner cost burden, housing problems, priority tenant pool, Hillsborough County, Tampa voucher rent, voucher underwriting, or affordable housing eligibility — no explicit invocation needed.

Prereq: HUD USER access token. Free — sign in at [huduser.gov](https://www.huduser.gov/) → User Profile → Access Token. Same token works across all four endpoints. Set as `HUD_API_KEY` env var.

## What's here

```
hud-real-estate/
  SKILL.md                              # Claude-facing frontmatter + body
  README.md                             # this file
  references/
    metrics.md                          # full 12-metric reference — key, extractor path, frequency, unit, verbatim rationale
    hud-datasets.yaml                   # canonical YAML catalog — API endpoints, benchmark geographies, Python snippets, CHAS derivations
```

`SKILL.md` carries the pushy description that controls when Claude loads the skill, plus the 3-category table, 6 decision playbooks, a minimal `requests`-based snippet covering FMR + CHAS, and the gotchas (county entityid routes to MSA for FMR, CHAS API coding ≠ CSV dictionary, string-cast counts before arithmetic, no `/mtspil/statedata`, no national AMI, USPS Vacancy restricted, CHAS 3-year release lag).

`references/metrics.md` is the one-page reference with every HUD metric, its extractor or CHAS derivation, and the investor rationale verbatim from the catalog. Includes a CHAS A-J group quick-reference for readers going beyond the 5 featured CHAS metrics. Load it when a specific metric or extractor is needed.

`references/hud-datasets.yaml` is the canonical catalog — the same shape TiRE uses internally, with 100% field coverage (API endpoint templates, Hillsborough × Florida × USA benchmark configuration where HUD publishes it, copy-paste Python snippets per metric, CHAS derivation blocks, bedroom-archive side-effect documentation).

## Source of truth

This skill is **mirrored** from `analyticsariel/tech-in-real-estate-ops` (private). The canonical HUD dataset catalog lives there at `agents/data/hud-datasets.yaml` and is the upstream of the YAML shipped here. If the private catalog changes, the mirror regenerates.

Live detail page on the TiRE site: <https://techinrealestate.com/skills/hud-real-estate>.

## License

MIT. Use, fork, adapt — credit TiRE if it helps you, and file issues in this repo if you find rough edges.
