# Goldenstat - Darttävlingsstatistik

En webbapplikation för att visa och analysera statistik från Stockholmsseriens och Riksseriens darttävlingar, samt cupturneringar.

## Projektstruktur

```
goldenstat/
├── app.py                      # Flask-app, config, delade helpers, blueprint-registrering
├── database.py                 # DartDatabase-klass (goldenstat.db / riksserien.db)
├── cup_database.py             # CupDatabase-klass (cups.db)
│
├── Routes (Flask Blueprints):
├── routes/
│   ├── __init__.py
│   ├── league.py               # Index, divisioner, ligor, top-stats, weekly-stats, overview
│   ├── players.py              # Spelarsök, spelarstatistik, kastdata
│   ├── matches.py              # Submatch, matchdetaljer, legs, seriematcher
│   ├── teams.py                # Lag, lineup, dubbel, klubbar
│   ├── tournaments.py          # Cupspel, cups.db (helt fristående)
│   └── tracking.py             # Analytics-endpoints
│
├── Databaser:
├── goldenstat.db               # Stockholmsserien - ligamatcher
├── riksserien.db               # Riksserien - ligamatcher
├── cups.db                     # Cupturneringar (separat schema)
│
├── Import-system:
├── daily_import.py             # Daglig import av nya ligamatcher
├── nightly_cup_import.py       # Nattlig import av nya cuper
├── import_cup.py               # CupImporter - import av enskild cup
├── new_season_importer.py      # Import av nya säsonger
├── smart_season_importer.py    # Smart import med spelarmappningar
├── smart_import_handler.py     # Smart player matching
├── generate_match_urls.py      # Generera match-URLer för import
│
├── Cache:
├── cache_warmup.py             # Cache warmup vid app-start
│
├── Frontend:
├── static/
│   ├── css/style.css           # Huvudstylesheet
│   └── js/app.js               # Frontend JavaScript
├── templates/
│   ├── base.html               # Bas-template med navigation
│   ├── index.html              # Huvudsida (spelare, lag, topplistor, veckans bästa)
│   ├── tournaments.html        # Cupspel (spelarsök, turneringslista, matchdetaljer)
│   ├── series_matches.html     # Seriematcher per vecka/division
│   ├── match_overview.html     # Matchöversikt
│   └── sub_match_throws.html   # Kastöversikt för en submatch
│
├── Automation:
├── .github/workflows/
│   ├── daily-import.yml        # Daglig ligaimport kl 02:00 UTC
│   ├── nightly-cup-import.yml  # Nattlig cupimport kl 04:00 UTC
│   └── pr-checks.yml           # Lint och import-test vid PR
│
├── Data:
├── current_match_urls/         # Match-URLer för aktuell säsong
├── import_logs/                # Importloggar (dagliga + cup)
│
└── archive/                    # Arkiverade script (ej aktiva)
```

## Installation

1. Installera dependencies:
```bash
pip install -r requirements.txt
```

2. Starta servern:
```bash
python app.py
```

3. Öppna webbläsaren: `http://localhost:3000`

Hoppa över cache warmup vid utveckling:
```bash
python app.py --no-warmup
```

## Databaser

Applikationen använder tre separata SQLite-databaser:

| Databas | Innehåll | Schema |
|---------|----------|--------|
| `goldenstat.db` | Stockholmsseriens ligamatcher | `database.py` |
| `riksserien.db` | Riksseriens ligamatcher | `database.py` (samma schema) |
| `cups.db` | Cupturneringar (n01-data) | `cup_database.py` (eget schema) |

Liga väljs via `?league=riksserien` i URL:en. Cupdata har helt separata routes under `/tournaments`.

## Import av data

### Daglig ligaimport (körs automatiskt kl 02:00 UTC)
```bash
python daily_import.py
```

### Nattlig cupimport (körs automatiskt kl 04:00 UTC)
```bash
python nightly_cup_import.py          # Importera nya cuper
python nightly_cup_import.py --dry    # Visa vad som skulle importeras
```

### Import av enskild cup
```bash
python import_cup.py t_ALIS_0219
```

### Import av ny säsong
```bash
python smart_season_importer.py
```

## Arkitektur

### Flask Blueprints

`app.py` (~200 rader) är entry point och registrerar 6 blueprints:

| Blueprint | Fil | Ansvar |
|-----------|-----|--------|
| `league_bp` | `routes/league.py` | Index, divisioner, ligor, top-stats, weekly-stats |
| `players_bp` | `routes/players.py` | Spelarsök, spelarstatistik, kastdata |
| `matches_bp` | `routes/matches.py` | Submatch, matchdetaljer, legs, seriematcher |
| `teams_bp` | `routes/teams.py` | Lag, lineup, dubbel, klubbar |
| `tournaments_bp` | `routes/tournaments.py` | Cupspel (egen databas cups.db) |
| `tracking_bp` | `routes/tracking.py` | Analytics-endpoints |

Delade helpers i `app.py`: `get_current_db()`, `get_current_db_path()`, `get_effective_sub_match_query()`, `get_effective_player_ids()`, `parse_match_position()`.

### Caching

Flask-Caching med FileSystemCache. Cache warmup vid start förpopulerar weekly-stats och top-stats för båda ligorna (Stockholmsserien + Riksserien).

### GitHub Actions

- **daily-import.yml**: Kör `daily_import.py` dagligen kl 02:00 UTC, committar uppdaterad `goldenstat.db`
- **nightly-cup-import.yml**: Kör `nightly_cup_import.py` kl 04:00 UTC (2h efter ligaimport), committar uppdaterad `cups.db`
- **pr-checks.yml**: Lint (flake8) och import-test vid pull requests

## Teknisk stack

- **Backend**: Python 3.11, Flask, Flask-Caching
- **Databas**: SQLite (3 separata databaser)
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Scraping**: Playwright (ligamatcher), Requests (cuper via n01 API)
- **Deploy**: Railway (Gunicorn)
- **CI/CD**: GitHub Actions

## Arkiverade filer

Gamla script och verktyg finns i `archive/`. Se `archive/README.md` för mer information.

---

*Senast uppdaterad: 2026-02-03*
