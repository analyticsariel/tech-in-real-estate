"""Build tire.db and the read-only corpus from the repo (decision #147).

    python -m tire_agent.build_db [--out tire_agent/build]

Inputs: agents/data/*.yaml catalogs, site/data/history/*.json,
site/data/readings/*.md, agents/data/skills.yaml + skill bodies,
agents/data/agents.yaml, site/app routes, and (Sprint 21, decision #192) the county geo store
site/data/geo/{state}/*.csv with agents/data/counties.yaml.

Fails loudly: every problem is collected and raised together, and nothing is
written unless the whole build succeeds. The output is swapped in atomically.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from tire_agent.summary import (
    FREQUENCIES,
    aligned_windows,
    forecast_horizons,
    is_forecast,
    summarize,
    value_at,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = Path(__file__).resolve().parent / "build"

SCHEMA = """
CREATE TABLE metrics (
  key TEXT PRIMARY KEY, source TEXT NOT NULL, label TEXT, title TEXT, units TEXT,
  frequency TEXT NOT NULL, category TEXT, geo_label TEXT, why_it_matters TEXT,
  url TEXT NOT NULL
);
CREATE TABLE observations (
  key TEXT NOT NULL, geo_key TEXT NOT NULL, geo_label TEXT, role TEXT NOT NULL,
  date TEXT NOT NULL, value REAL NOT NULL, quality TEXT,
  PRIMARY KEY (key, geo_key, role, date)
) WITHOUT ROWID;  -- the key is the lookup path; a separate index doubled the file (#192)
CREATE TABLE metric_summary (
  key TEXT NOT NULL, geo_key TEXT NOT NULL, geo_label TEXT, role TEXT NOT NULL,
  units TEXT, frequency TEXT,
  latest_date TEXT, latest_value REAL,
  from_date_1m TEXT, from_value_1m REAL, change_1m REAL, pct_change_1m REAL, direction_1m TEXT,
  from_date_3m TEXT, from_value_3m REAL, change_3m REAL, pct_change_3m REAL, direction_3m TEXT,
  from_date_12m TEXT, from_value_12m REAL, change_12m REAL, pct_change_12m REAL, direction_12m TEXT,
  streak_count INTEGER, streak_direction TEXT,
  aligned_date TEXT, aligned_value REAL,
  aligned_from_date_1m TEXT, aligned_from_value_1m REAL, aligned_change_1m REAL, aligned_pct_change_1m REAL,
  aligned_direction_1m TEXT,
  aligned_from_date_3m TEXT, aligned_from_value_3m REAL, aligned_change_3m REAL, aligned_pct_change_3m REAL,
  aligned_direction_3m TEXT,
  aligned_from_date_12m TEXT, aligned_from_value_12m REAL, aligned_change_12m REAL, aligned_pct_change_12m REAL,
  aligned_direction_12m TEXT,
  is_forecast INTEGER NOT NULL,
  url TEXT NOT NULL
);
-- Florida county views (S21.H, #192), kept out of metric_summary so `WHERE key = ...` there still returns
-- one page's primary + benchmarks. One row per metric x county, resolved like the site's picker.
CREATE TABLE county_summary (
  key TEXT NOT NULL, county TEXT NOT NULL, geo_key TEXT NOT NULL, geo_label TEXT, grain TEXT NOT NULL,
  units TEXT, frequency TEXT,
  latest_date TEXT, latest_value REAL,
  from_date_1m TEXT, from_value_1m REAL, change_1m REAL, pct_change_1m REAL, direction_1m TEXT,
  from_date_3m TEXT, from_value_3m REAL, change_3m REAL, pct_change_3m REAL, direction_3m TEXT,
  from_date_12m TEXT, from_value_12m REAL, change_12m REAL, pct_change_12m REAL, direction_12m TEXT,
  streak_count INTEGER, streak_direction TEXT,
  thin_latest INTEGER NOT NULL, thin_12m INTEGER NOT NULL,
  is_forecast INTEGER NOT NULL,
  url TEXT NOT NULL,
  PRIMARY KEY (key, county)
);
CREATE TABLE county_forecasts (
  key TEXT NOT NULL, county TEXT NOT NULL, geo_key TEXT NOT NULL, geo_label TEXT,
  base_month TEXT NOT NULL, horizon_months INTEGER NOT NULL, target_month TEXT NOT NULL,
  value REAL NOT NULL, is_past INTEGER NOT NULL, url TEXT NOT NULL
);
CREATE TABLE counties (
  fips TEXT PRIMARY KEY, slug TEXT NOT NULL, name TEXT NOT NULL, population INTEGER,
  metro_cbsa TEXT, metro_title TEXT, aliases TEXT
);
CREATE TABLE places (term TEXT NOT NULL, fips TEXT NOT NULL, slug TEXT NOT NULL, ambiguous INTEGER NOT NULL);
CREATE TABLE forecasts (
  key TEXT NOT NULL, geo_key TEXT NOT NULL, geo_label TEXT, role TEXT NOT NULL,
  base_month TEXT NOT NULL, horizon_months INTEGER NOT NULL, target_month TEXT NOT NULL,
  value REAL NOT NULL, is_past INTEGER NOT NULL, url TEXT NOT NULL
);
CREATE TABLE routes (url TEXT PRIMARY KEY, kind TEXT NOT NULL);
CREATE VIRTUAL TABLE pages USING fts5(
  kind, key, title, url UNINDEXED, tags, body, tokenize = 'porter unicode61'
);
CREATE TABLE build_info (name TEXT PRIMARY KEY, value TEXT);
"""


class BuildError(Exception):
    """Raised with every problem found, so one run shows all of them."""


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def load_metric_catalog(repo: Path) -> list[dict]:
    """Mirror site/lib/metric-entry.ts allMetricEntries: FRED + every source's datasets."""
    out = []
    for e in _yaml(repo / "agents/data/fred-series.yaml").get("series", []):
        out.append({**e, "source": "fred"})
    for src in _yaml(repo / "agents/data/sources.yaml").get("sources", []):
        if src["key"] == "fred":
            continue
        for e in _yaml(repo / src["dataset_catalog"]).get("datasets", []):
            out.append({**e, "source": src["key"]})
    return out


def static_routes(repo: Path) -> list[str]:
    """Static site/app routes, minus any page that renders ComingSoonSection."""
    app = repo / "site/app"
    routes = []
    for page in sorted(app.rglob("page.tsx")):
        rel = page.parent.relative_to(app).as_posix()
        if "[" in rel or "ComingSoonSection" in page.read_text():
            continue
        routes.append("/" if rel == "." else f"/{rel}")
    return routes


def page_meta(repo: Path, route: str) -> tuple[str, str]:
    page = repo / "site/app" / route.strip("/") / "page.tsx"
    text = page.read_text()
    title = re.search(r'title:\s*"([^"]+)"', text)
    desc = re.search(r'description:\s*\n?\s*"([^"]+)"', text)
    return (title.group(1) if title else route), (desc.group(1) if desc else "")


def series_for(key: str, history: dict, entry: dict) -> list[dict]:
    """Primary + benchmark series; national FRED-style files become one primary series."""
    if history.get("series"):
        return history["series"]
    geo_label = (
        history.get("featured_geo_label")
        or entry.get("featured_geo_label")
        or "United States"
    )
    return [
        {
            "geo_key": entry.get("featured_geo") or "us_1",
            "geo_label": geo_label,
            "role": "primary",
            "observations": history["observations"],
        }
    ]


# The site's default county view (site/lib/county-view.ts DEFAULT_COUNTY, #190). Its canonical URL is the plain
# metric page: the picker drops ?county= for it, so the agent must cite it without the parameter.
DEFAULT_COUNTY = "hillsborough"

# Bare county names that are also everyday words. In a question they mean the county only when followed
# by "county" or written capitalized ("Lake", not "lake view"); the rest ("manatee", "pinellas") always do.
AMBIGUOUS_NAMES = {
    "baker", "bay", "citrus", "clay", "columbia", "franklin", "glades", "gulf", "hamilton", "highlands",
    "holmes", "jackson", "jefferson", "lake", "lee", "levy", "liberty", "madison", "marion", "monroe",
    "orange", "taylor", "union", "washington",
}  # fmt: skip


def load_counties(repo: Path) -> dict:
    """counties.yaml (decision #173) indexed for the build: counties, metro titles, state."""
    cat = _yaml(repo / "agents/data/counties.yaml")
    return {
        "state": cat["state"],
        "counties": cat["counties"],
        "metro_titles": {m["cbsa"]: m["title"] for m in cat["metros"]},
    }


def county_label(c: dict, state: dict) -> str:
    return f"{c['name']}, {state['name']}"


def place_rows(geo: dict) -> list[tuple]:
    """(term, fips, slug, ambiguous) for county names, bare names and aliases (#189), lower-cased."""
    rows = []
    for c in geo["counties"]:
        bare = c["name"].removesuffix(" County").lower()
        rows.append((f"{bare} county", c["fips"], c["slug"], 0))
        rows.append((bare, c["fips"], c["slug"], int(bare in AMBIGUOUS_NAMES)))
        rows += [(a.lower(), c["fips"], c["slug"], 0) for a in c.get("aliases") or []]
    return rows


def read_geo_csv(path: Path) -> dict[tuple[str, str], list[dict]]:
    """{(geo_type, geo_id): ascending [{date, value, quality}]} from one store file (#175)."""
    out: dict[tuple[str, str], list[dict]] = {}
    with path.open() as f:
        for r in csv.DictReader(f):
            out.setdefault((r["geo_type"], r["geo_id"]), []).append(
                {"date": r["date"], "value": float(r["value"]), "quality": r["quality"]}
            )
    for obs in out.values():
        obs.sort(key=lambda o: o["date"])
    return out


def county_view(
    geos: dict, county: dict, metro_titles: dict, state: dict
) -> tuple[str, str, str, list[dict]] | None:
    """The picker's rule (#190): the county's rows, else its metro's, else None (not published).
    Returns (grain, geo_key, geo_label, obs)."""
    own = geos.get(("county", county["fips"]))
    if own:
        return "county", f"county_{county['fips']}", county_label(county, state), own
    metro = county.get("metro")
    if metro and geos.get(("metro", metro)):
        return "metro", f"metro_{metro}", metro_titles[metro], geos[("metro", metro)]
    return None


def thin_counts(obs: list[dict], from_date_12m: str | None) -> tuple[int, int]:
    """(latest is thin, thin points in the 12-month window after from_date_12m through latest)."""
    latest_thin = int(obs[-1].get("quality") == "thin")
    start = from_date_12m or obs[-1]["date"]
    window = [o for o in obs if o["date"] > start] or obs[-1:]
    return latest_thin, sum(o.get("quality") == "thin" for o in window)


def geo_rows(
    e: dict, url: str, freq: str, path: Path, geo: dict, today: dt.date
) -> tuple[list, list, list, list[str]]:
    """Store rows for one metric: observations once per real geography, plus one summary row per county
    (role 'county') resolved like the picker, citing the exact ?county= view."""
    geos = read_geo_csv(path)
    obs_rows, summary_rows, forecast_rows, urls = [], [], [], []
    for (gtype, gid), obs in geos.items():
        # geo_label stays NULL on store rows: it would repeat on every month of ~500k rows, and
        # metric_summary / counties carry it (#192).
        obs_rows += [
            (
                e["key"],
                f"{gtype}_{gid}",
                None,
                gtype,
                o["date"],
                o["value"],
                o["quality"],
            )
            for o in obs
        ]
    horizons = e.get("forecast_horizons_months")
    for c in geo["counties"]:
        view = county_view(geos, c, geo["metro_titles"], geo["state"])
        if view is None:
            continue
        grain, geo_key, label, obs = view
        county_url = url if c["slug"] == DEFAULT_COUNTY else f"{url}?county={c['slug']}"
        row = summarize(obs, freq, e.get("units"))
        if horizons:
            try:
                fc = forecast_horizons(obs, horizons, today)
            except ValueError:
                continue  # a geography without the full horizon set isn't a forecast we can state
            forecast_rows += [
                (e["key"], c["slug"], geo_key, label, *r.values(), county_url)
                for r in fc
            ]
            row["streak_count"] = row["streak_direction"] = None
        thin_latest, thin_12m = thin_counts(obs, row.get("from_date_12m"))
        summary_rows.append(
            {
                "key": e["key"],
                "county": c["slug"],
                "geo_key": geo_key,
                "geo_label": label,
                "grain": grain,
                "units": e.get("units"),
                "frequency": freq,
                **row,
                "thin_latest": thin_latest,
                "thin_12m": thin_12m,
                "is_forecast": int(
                    bool(horizons) or is_forecast(row["latest_date"], freq, today)
                ),
                "url": county_url,
            }
        )
        urls.append(county_url)
    return obs_rows, summary_rows, forecast_rows, urls


def git_sha(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build(repo: Path, out: Path, sha: str, today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    problems: list[str] = []
    catalog = load_metric_catalog(repo)
    skills = _yaml(repo / "agents/data/skills.yaml").get("skills", [])
    agents = _yaml(repo / "agents/data/agents.yaml").get("agents", [])
    routes = {r: "page" for r in static_routes(repo)}
    # The county layer is optional so a repo without it still builds; the golden set's county records
    # can't resolve without it, so the eval gate catches a missing catalog in a real build.
    geo = load_counties(repo) if (repo / "agents/data/counties.yaml").exists() else None
    geo_dir = repo / "site/data/geo" / geo["state"]["abbr"].lower() if geo else None
    county_rows, county_fc_rows = [], []

    metric_rows, obs_rows, summary_rows, page_rows, forecast_rows = [], [], [], [], []
    for e in catalog:
        key, url = e["key"], f"/metric/{e['source']}/{e['key']}"
        hist_path = repo / "site/data/history" / f"{key}.json"
        if not hist_path.exists():
            problems.append(f"{url}: missing {hist_path.relative_to(repo)}")
            continue
        history = json.loads(hist_path.read_text())
        freq = history.get("frequency") or e.get("frequency")
        if freq not in FREQUENCIES:
            problems.append(f"{url}: unknown frequency {freq!r}")
            continue
        series = series_for(key, history, e)
        primary = [s for s in series if s.get("role") == "primary"]
        if len(primary) != 1 or not primary[0]["observations"]:
            problems.append(
                f"{url}: needs exactly one primary series with observations"
            )
            continue
        routes[url] = "metric"
        geo_label = primary[0]["geo_label"]
        metric_rows.append(
            (
                key,
                e["source"],
                e.get("label"),
                e.get("full_title"),
                e.get("units"),
                freq,
                e.get("category"),
                geo_label,
                e.get("why_it_matters"),
                url,
            )
        )
        primary_latest = dt.date.fromisoformat(primary[0]["observations"][-1]["date"])
        for s in series:
            obs = s["observations"]
            if not obs:
                problems.append(f"{url}: {s['geo_key']} has no observations")
                continue
            obs_rows += [
                (
                    key,
                    s["geo_key"],
                    s["geo_label"],
                    s["role"],
                    o["date"],
                    o["value"],
                    None,
                )
                for o in obs
            ]
            row = summarize(obs, freq, e.get("units"))
            horizons = e.get("forecast_horizons_months")
            if horizons:
                try:
                    fc = forecast_horizons(obs, horizons, today)
                except ValueError as err:
                    problems.append(f"{url}: {s['geo_key']} {err}")
                    continue
                forecast_rows += [
                    (key, s["geo_key"], s["geo_label"], s["role"], *r.values(), url)
                    for r in fc
                ]
                # Horizons aren't a time series: a "streak" across them means nothing.
                row["streak_count"] = row["streak_direction"] = None
            aligned = (
                value_at(obs, freq, primary_latest) if s["role"] != "primary" else None
            )
            aligned_cols = (
                aligned_windows(obs, freq, e.get("units"), aligned["date"])
                if aligned
                else aligned_windows([], freq, e.get("units"), "")
            )
            summary_rows.append(
                {
                    "key": key,
                    "geo_key": s["geo_key"],
                    "geo_label": s["geo_label"],
                    "role": s["role"],
                    "units": e.get("units"),
                    "frequency": freq,
                    **row,
                    "aligned_date": aligned and aligned["date"],
                    "aligned_value": aligned and aligned["value"],
                    **aligned_cols,
                    "is_forecast": int(
                        bool(horizons) or is_forecast(row["latest_date"], freq, today)
                    ),
                    "url": url,
                }
            )
        geo_csv = geo_dir / f"{key}.csv" if geo_dir else None
        if geo_csv and geo_csv.exists():
            g_obs, g_summary, g_fc, g_urls = geo_rows(e, url, freq, geo_csv, geo, today)
            obs_rows += g_obs
            county_rows += g_summary
            county_fc_rows += g_fc
            routes.update(dict.fromkeys(g_urls, "metric"))
        # pages(kind, key, title, url, tags, body): tags carry label, geography, category so a search for
        # "Tampa rent" finds ZORI even though its title says neither word.
        tags = " ".join(
            str(x)
            for x in [
                e.get("label"),
                geo_label,
                e.get("category"),
                e.get("units"),
                e["source"],
                " ".join(e.get("tags") or []),
            ]
            if x
        )
        title = e.get("full_title") or e.get("label")
        page_rows.append(
            ("metric", key, title, url, tags, e.get("why_it_matters") or "")
        )
        reading = repo / "site/data/readings" / f"{key}.md"
        if reading.exists():
            body = reading.read_text().split("---", 2)[-1].strip()
            page_rows.append(
                ("reading", key, f"Weekly reading: {e.get('label')}", url, tags, body)
            )

    corpus_files: dict[str, str] = {}
    for s in skills:
        url = f"/skills/{s['key']}"
        routes[url] = "skill"
        skill_text = ""
        if s.get("status") == "shipped":
            skill_md = repo / s.get("skill_dir", "") / "SKILL.md"
            if not skill_md.exists():
                problems.append(
                    f"{url}: shipped skill missing {skill_md.relative_to(repo)}"
                )
                continue
            skill_text = skill_md.read_text()
            corpus_files[f"skills/{s['key']}.md"] = (
                f"---\nurl: {url}\n---\n{skill_text}"
            )
        tags = f"{s.get('name')} skill {s.get('one_liner') or ''}"
        body = " ".join(
            p for p in [s.get("why_it_matters"), s.get("description"), skill_text] if p
        )
        page_rows.append(("skill", s["key"], s.get("name"), url, tags, body))

    # The site renders /agents/{key} for every agents.yaml entry (generateStaticParams), so the detail pages
    # are live exactly when /agents is. Their status says whether readers can use the agent yet.
    if "/agents" in routes:
        for a in agents:
            url = f"/agents/{a['key']}"
            routes[url] = "agent"
            tags = f"{a.get('name')} agent {a.get('status')} {a.get('one_liner') or ''}"
            body = f"Status: {a.get('status')}. {a.get('why_it_matters') or ''}"
            if a.get("try_url"):
                body += f" Try it at {a['try_url']}."
            page_rows.append(("agent", a["key"], a.get("name"), url, tags, body))

    for route, kind in list(routes.items()):
        if kind == "page":
            title, desc = page_meta(repo, route)
            page_rows.append(("page", route, title, route, title, desc))

    if not metric_rows:
        problems.append("no metrics built")
    unknown = sorted({r[3] for r in page_rows} - set(routes))
    if unknown:
        problems.append(f"pages point at non-live routes: {unknown}")
    if problems:
        raise BuildError("tire.db build failed:\n  - " + "\n  - ".join(problems))

    corpus_files["INDEX.md"] = (
        "# TiRE corpus (read-only)\n"
        "- Numbers live in tire.db: use the `search` and `query` tools, never these files.\n"
        "- /corpus/skills/{key}.md: full body of each shipped Claude skill (url in frontmatter).\n"
        "- The blog, /mcp and /community are coming soon. There is nothing to cite there yet.\n"
    )

    tmp = Path(tempfile.mkdtemp(prefix="tire-build-", dir=out.parent))
    try:
        db = sqlite3.connect(tmp / "tire.db")
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO metrics VALUES (?,?,?,?,?,?,?,?,?,?)", metric_rows)
        db.executemany("INSERT INTO observations VALUES (?,?,?,?,?,?,?)", obs_rows)
        db.executemany(
            "INSERT INTO counties VALUES (?,?,?,?,?,?,?)",
            []
            if not geo
            else [
                (
                    c["fips"],
                    c["slug"],
                    county_label(c, geo["state"]),
                    c.get("population"),
                    c.get("metro"),
                    geo["metro_titles"].get(c.get("metro")),
                    ", ".join(c.get("aliases") or []),
                )
                for c in geo["counties"]
            ],
        )
        db.executemany(
            "INSERT INTO places VALUES (?,?,?,?)", place_rows(geo) if geo else []
        )
        cols = list(summary_rows[0])
        db.executemany(
            f"INSERT INTO metric_summary ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
            [tuple(r[c] for c in cols) for r in summary_rows],
        )
        db.executemany(
            "INSERT INTO forecasts VALUES (?,?,?,?,?,?,?,?,?,?)", forecast_rows
        )
        if county_rows:
            ccols = list(county_rows[0])
            db.executemany(
                f"INSERT INTO county_summary ({','.join(ccols)}) VALUES ({','.join('?' * len(ccols))})",
                [tuple(r[c] for c in ccols) for r in county_rows],
            )
        db.executemany(
            "INSERT INTO county_forecasts VALUES (?,?,?,?,?,?,?,?,?,?)", county_fc_rows
        )
        db.executemany("INSERT INTO routes VALUES (?,?)", sorted(routes.items()))
        db.executemany("INSERT INTO pages VALUES (?,?,?,?,?,?)", page_rows)
        counts = {
            t: db.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            for t in (
                "metrics",
                "observations",
                "metric_summary",
                "forecasts",
                "routes",
                "pages",
                "county_summary",
                "county_forecasts",
                "counties",
            )
        }
        info = {
            "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            "git_sha": sha,
            **{f"count_{k}": str(v) for k, v in counts.items()},
        }
        db.executemany("INSERT INTO build_info VALUES (?,?)", info.items())
        db.commit()
        db.close()
        for rel, text in corpus_files.items():
            p = tmp / "corpus" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        if out.exists():
            shutil.rmtree(out)
        tmp.rename(out)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    try:
        info = build(REPO_ROOT, args.out.resolve(), git_sha(REPO_ROOT))
    except BuildError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(json.dumps(info, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
