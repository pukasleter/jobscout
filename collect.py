#!/usr/bin/env python3
"""
Job-Agent Collector
-------------------
Sammelt täglich Stellen aus
  - Bundesagentur für Arbeit (inoffizielle, aber öffentliche REST-API)
  - Google Jobs via SerpApi        (env: SERPAPI_KEY)
  - LinkedIn via Apify-Actor       (env: APIFY_TOKEN)

normalisiert sie, filtert harte Ausschlüsse, entfernt Duplikate (auch
quellenübergreifend) und schreibt nur NEUE Stellen nach data/jobs.json.
Recherche und Bewertung übernimmt danach die Claude-Aufgabe.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SEEN_FILE = DATA / "seen.json"
JOBS_FILE = DATA / "jobs.json"
ARCHIVE = DATA / "archive"

UA = {"User-Agent": "job-agent/1.0 (private job search)"}
TODAY = dt.date.today()


# ------------------------------------------------------------ helpers
def log(msg: str) -> None:
    print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


def norm(s: str | None) -> str:
    """Normalisiert Titel/Firmen für die Duplikaterkennung."""
    s = (s or "").lower()
    s = re.sub(r"\((m|w|d|f|x|h|gn|all genders?)([/|,]\s*(m|w|d|f|x|h|gn))*\)", " ", s)
    s = re.sub(r"\b(m/w/d|w/m/d|m/f/d|f/m/d|all genders?|w/m/x)\b", " ", s)
    s = re.sub(r"\b(gmbh|ag|se|kg|e\.?\s?v\.?|mbh|co\.?|inc|ltd|sa|sàrl)\b", " ", s)
    s = re.sub(r"[^a-z0-9äöüß]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def dedup_key(title: str, company: str) -> str:
    return hashlib.sha1(f"{norm(title)}|{norm(company)}".encode()).hexdigest()[:16]


def clip(text: str | None, n: int) -> str:
    text = re.sub(r"\s+\n", "\n", (text or "")).strip()
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + " …"


def job(source, title, company, location, url, *, country=None, posted=None,
        description=None, salary=None, via=None, extra=None) -> dict:
    return {
        "source": source,
        "title": (title or "").strip(),
        "company": (company or "").strip(),
        "location": (location or "").strip(),
        "country": country,
        "url": url,
        "posted": posted,
        "salary": salary,
        "via": via,
        "description": description or "",
        "extra": extra or {},
    }


# ------------------------------------------------------------ sources
def fetch_ba(cfg: dict) -> list[dict]:
    sc = cfg["sources"]["ba"]
    base = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
    headers = {**UA, "X-API-Key": "jobboerse-jobsuche"}
    out: list[dict] = []
    for loc in cfg["locations"]["ba"]:
        for q in cfg["queries"]["de"]:
            params = {
                "was": q, "wo": loc["wo"], "umkreis": loc.get("umkreis", 50),
                "veroeffentlichtseit": cfg["days_back"], "size": sc.get("page_size", 50),
                "page": 1, "angebotsart": sc.get("angebotsart", 1),
                "zeitarbeit": str(cfg["exclude"].get("zeitarbeit", False)).lower(),
            }
            data = None
            for path in ("/pc/v6/jobs", "/pc/v4/app/jobs", "/pc/v4/jobs"):
                r = requests.get(base + path, params=params, headers=headers, timeout=30)
                if r.status_code == 200:
                    data = r.json()
                    break
            if data is None:
                raise RuntimeError(f"BA: keine Antwort ({r.status_code})")
            for s in data.get("stellenangebote", []) or []:
                ort = s.get("arbeitsort") or {}
                out.append(job(
                    "arbeitsagentur", s.get("titel") or s.get("beruf"), s.get("arbeitgeber"),
                    " ".join(filter(None, [ort.get("plz"), ort.get("ort")])),
                    f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{s.get('refnr')}",
                    country="DE",
                    posted=s.get("aktuelleVeroeffentlichungsdatum") or s.get("modifikationsTimestamp"),
                    extra={"refnr": s.get("refnr"), "query": q},
                ))
            time.sleep(0.5)
    return out


def enrich_ba_details(jobs: list[dict], cfg: dict) -> None:
    """Lädt Beschreibungstexte nur für neue BA-Stellen nach."""
    base = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobdetails/"
    headers = {**UA, "X-API-Key": "jobboerse-jobsuche"}
    for j in jobs:
        refnr = j["extra"].get("refnr")
        if "arbeitsagentur" not in j["sources"] or not refnr:
            continue
        try:
            enc = base64.b64encode(refnr.encode()).decode()
            r = requests.get(base + enc, headers=headers, timeout=30)
            if r.ok:
                d = r.json()
                j["description"] = d.get("stellenangebotsBeschreibung") or ""
                j["extra"]["befristung"] = d.get("befristung")
                j["extra"]["arbeitszeit"] = d.get("arbeitszeitmodelle")
            time.sleep(0.3)
        except Exception as e:  # Details sind nice-to-have
            log(f"BA-Details {refnr}: {e}")


def fetch_serpapi(cfg: dict) -> list[dict]:
    key = os.environ.get("SERPAPI_KEY")
    if not key:
        raise RuntimeError("SERPAPI_KEY fehlt")
    sc = cfg["sources"]["serpapi"]
    combos = []
    for loc in cfg["locations"]["serpapi"]:
        qs = cfg["queries"]["ch" if loc.get("gl") == "ch" else "de"]
        combos += [(q, loc) for q in qs]
    # Rotation: jeden Tag ein anderes Fenster der Kombinationen
    budget = min(sc.get("max_requests_per_run", 8), len(combos))
    start = (TODAY.toordinal() * budget) % len(combos)
    todays = [combos[(start + i) % len(combos)] for i in range(budget)]
    log(f"SerpApi: {budget} von {len(combos)} Kombinationen heute")

    out: list[dict] = []
    for q, loc in todays:
        params = {"engine": "google_jobs", "q": q, "location": loc["location"],
                  "gl": loc.get("gl", "de"), "hl": loc.get("hl", "de"), "api_key": key}
        if loc.get("lrad"):
            params["lrad"] = loc["lrad"]
        r = requests.get("https://serpapi.com/search.json", params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
        if "error" in data and "hasn't returned any results" not in data["error"]:
            raise RuntimeError(f"SerpApi: {data['error']}")
        for s in data.get("jobs_results", []) or []:
            ext = s.get("detected_extensions") or {}
            apply = s.get("apply_options") or []
            out.append(job(
                "google_jobs", s.get("title"), s.get("company_name"), s.get("location"),
                (apply[0].get("link") if apply else None) or s.get("share_link"),
                country=loc.get("gl", "").upper(), posted=ext.get("posted_at"),
                description=s.get("description"), salary=ext.get("salary"),
                via=s.get("via"),
                extra={"schedule": ext.get("schedule_type"), "query": q,
                       "apply_links": [a.get("link") for a in apply[:4]]},
            ))
    return out


def _pick(d: dict, *keys):
    for k in keys:
        v = d.get(k)
        if isinstance(v, dict):
            v = v.get("name") or v.get("text")
        if v:
            return v
    return None


def fetch_linkedin(cfg: dict) -> list[dict]:
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise RuntimeError("APIFY_TOKEN fehlt")
    sc = cfg["sources"]["linkedin"]
    keywords = sorted(set(cfg["queries"]["de"] + cfg["queries"]["ch"]))
    payload = {
        "keywords": keywords,
        "locations": cfg["locations"]["linkedin"],
        "datePosted": sc.get("date_posted", "past 24 hours"),
        "scrapeJobDetails": sc.get("scrape_details", True),
        "maxItems": sc.get("max_items", 150),
        "proxyConfiguration": {"useApifyProxy": True},
    }
    url = (f"https://api.apify.com/v2/acts/{sc['actor']}/run-sync-get-dataset-items"
           f"?timeout={sc.get('timeout_s', 280)}")
    r = requests.post(url, json=payload, timeout=sc.get("timeout_s", 280) + 30,
                      headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    items = r.json()
    out: list[dict] = []
    for s in items if isinstance(items, list) else []:
        title = _pick(s, "title", "jobTitle", "position")
        if not title:            # z. B. Summary-Datensätze des Actors
            continue
        loc = _pick(s, "location", "jobLocation", "place") or ""
        out.append(job(
            "linkedin", title, _pick(s, "company", "companyName", "company_name"), loc,
            _pick(s, "url", "jobUrl", "link", "linkedinUrl", "applyUrl"),
            country="CH" if re.search(r"switzerland|schweiz|suisse", loc, re.I) else
                    ("DE" if re.search(r"germany|deutschland", loc, re.I) else None),
            posted=_pick(s, "postedAt", "publishedAt", "postedDate", "listedAt", "datePosted"),
            description=_pick(s, "description", "descriptionText", "jobDescription"),
            salary=_pick(s, "salary", "salaryInfo", "compensation"),
            extra={"seniority": _pick(s, "seniorityLevel", "experienceLevel"),
                   "employment_type": _pick(s, "employmentType", "contractType"),
                   "applicants": _pick(s, "applicantsCount", "applicants")},
        ))
    return out


# ------------------------------------------------------------ pipeline
def excluded(j: dict, cfg: dict) -> bool:
    ex = cfg.get("exclude", {})
    for pat in ex.get("title_patterns", []):
        if re.search(pat, j["title"], re.I):
            return True
    comp = norm(j["company"])
    return any(norm(c) and norm(c) in comp for c in ex.get("companies", []))


def main() -> int:
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    DATA.mkdir(exist_ok=True)
    ARCHIVE.mkdir(exist_ok=True)
    seen: dict = json.loads(SEEN_FILE.read_text()) if SEEN_FILE.exists() else {}

    fetchers = {"arbeitsagentur": ("ba", fetch_ba),
                "google_jobs": ("serpapi", fetch_serpapi),
                "linkedin": ("linkedin", fetch_linkedin)}
    raw: list[dict] = []
    stats, errors = {}, {}
    for name, (key, fn) in fetchers.items():
        if not cfg["sources"].get(key, {}).get("enabled", False):
            stats[name] = "deaktiviert"
            continue
        try:
            res = fn(cfg)
            stats[name] = len(res)
            raw += res
            log(f"{name}: {len(res)} Treffer")
        except Exception as e:
            errors[name] = str(e)[:300]
            log(f"FEHLER {name}: {e}")

    # Filtern + Duplikate zusammenführen
    merged: dict[str, dict] = {}
    n_excluded = 0
    for j in raw:
        if not j["title"] or excluded(j, cfg):
            n_excluded += 1
            continue
        k = dedup_key(j["title"], j["company"])
        if k in merged:
            m = merged[k]
            if j["source"] not in m["sources"]:
                m["sources"].append(j["source"])
                m["links"][j["source"]] = j["url"]
            if len(j["description"]) > len(m["description"]):
                m["description"] = j["description"]
            m["salary"] = m["salary"] or j["salary"]
            continue
        j["id"] = k
        j["sources"] = [j.pop("source")]
        j["links"] = {j["sources"][0]: j["url"]}
        merged[k] = j

    new = [j for k, j in merged.items() if k not in seen]
    if cfg["sources"].get("ba", {}).get("fetch_details"):
        enrich_ba_details([j for j in new if "arbeitsagentur" in j["sources"]], cfg)
    for j in new:
        j["description"] = clip(j["description"], cfg.get("max_description_chars", 4000))
        j["first_seen"] = TODAY.isoformat()
        seen[j["id"]] = TODAY.isoformat()

    # alte Einträge vergessen
    cutoff = (TODAY - dt.timedelta(days=cfg.get("seen_retention_days", 90))).isoformat()
    seen = {k: v for k, v in seen.items() if v >= cutoff}

    result = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "stats": {"raw_per_source": stats, "excluded": n_excluded,
                  "unique": len(merged), "new": len(new)},
        "errors": errors,
        "jobs": new,
    }
    JOBS_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    (ARCHIVE / f"{TODAY.isoformat()}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    SEEN_FILE.write_text(json.dumps(seen, indent=0), encoding="utf-8")
    log(f"Fertig: {len(new)} neue Stellen, Fehler: {list(errors) or 'keine'}")
    # Nur scheitern (-> GitHub schickt Fehler-Mail), wenn ALLE aktiven Quellen ausfallen
    active = [n for n, v in stats.items() if v != "deaktiviert"] + list(errors)
    return 1 if active and set(active) == set(errors) else 0


if __name__ == "__main__":
    sys.exit(main())
