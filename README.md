# Job-Agent

Tägliche, KI-gestützte Jobsuche (Soziologie, Raum Konstanz + Schweizer Grenzregion).

```
06:00  GitHub Actions ── collect.py ──► data/jobs.json   (nur neue Stellen)
         ├─ Arbeitsagentur (API, kostenlos)
         ├─ Google Jobs via SerpApi (enthält viele StepStone/Indeed/Firmen-Anzeigen)
         └─ LinkedIn via Apify
06:51  Claude-Aufgabe (Cowork, Mo–Fr)
         ├─ liest data/jobs.json (öffentlich über raw.githubusercontent.com)
         ├─ sucht zusätzlich direkt: Städte, Kantone, Hochschulen, StepStone, sozjobs.ch …
         ├─ recherchiert, bewertet gegen das Profil (+ Rückmeldungen aus dem Tracker)
         ├─ trägt Gemeldetes in die Tracker-Seite „Job-Scout Treffer“ ein
         └─ Mail an Lukas → Weiterleitungsregel an sie
```

## Einrichtung (ca. 20 Minuten)

### 1. Repo anlegen
- Auf GitHub ein **öffentliches** Repo anlegen, z. B. `job-agent`. Öffentlich,
  weil die Claude-Aufgabe nur so `jobs.json` lesen kann. Im Repo stehen nur
  Suchbegriffe und öffentliche Stellenanzeigen – kein Name, kein Profil.
- Alle Dateien aus diesem Ordner hochladen (inkl. `.github/` und `data/`).

### 2. API-Zugänge holen
| Dienst | Wo | Hinweis |
|---|---|---|
| SerpApi | serpapi.com → Registrieren → Dashboard → *API Key* | Free-Kontingent reicht für `max_requests_per_run: 8` evtl. knapp; ggf. auf 5 reduzieren |
| Apify | apify.com → Registrieren → *Settings → API & Integrations* → Personal API token | Actor `jmlp/linkedin-jobs-scraper` einmal im Store öffnen; Kosten laut Anbieter < 1 $ pro 1.000 Stellen |

### 3. Secrets im Repo hinterlegen
*Settings → Secrets and variables → Actions → New repository secret*
- `SERPAPI_KEY`
- `APIFY_TOKEN`

### 4. Ersten Lauf manuell starten
*Actions → „Jobs sammeln“ → Run workflow*. Für den ersten Lauf in `config.yaml`
`days_back: 14` setzen (Grundstock), danach wieder auf `2`.

Log prüfen: pro Quelle steht dort die Trefferzahl oder der Fehler. Fällt eine
einzelne Quelle aus, läuft der Rest weiter; nur wenn alle ausfallen, schlägt der
Lauf fehl (→ GitHub schickt dir eine Mail).

### 5. Repo-Namen an Claude geben
`owner/repo` an Claude geben → Claude trägt ihn in die tägliche Aufgabe ein.

## Anpassen
Alles Fachliche steht in `config.yaml` (Suchbegriffe, Orte, Ausschlüsse).
Die Bewertungslogik (was „passt“) steht im Prompt der Claude-Aufgabe,
liegt bewusst NICHT im Repo (enthält persönliche Daten), sondern nur in der Claude-Aufgabe.

## Dateien
| Datei | Zweck |
|---|---|
| `collect.py` | Sammeln, filtern, Duplikate entfernen |
| `config.yaml` | Suchbegriffe, Orte, Quellen, Ausschlüsse |
| `data/jobs.json` | Neue Stellen des letzten Laufs (Input für Claude) |
| `data/seen.json` | Gedächtnis des Collectors (90 Tage) |
| `data/archive/` | Tagesstände zum Nachschauen |

## Bekannte Grenzen
- LinkedIn/Google Jobs laufen über Drittanbieter. Ändert LinkedIn etwas, kann die
  Quelle ein paar Tage ausfallen – der Digest weist darauf hin.
- Die Arbeitsagentur-API ist öffentlich, aber nicht offiziell dokumentiert; der
  Collector probiert mehrere Endpunkt-Versionen.
- GitHub startet geplante Läufe teils verspätet (meist Minuten).
