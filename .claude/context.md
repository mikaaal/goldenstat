# Goldenstat Project Context

## IMPORTANT: Windows-specific rules
- NEVER redirect output to `nul` or `NUL`. On Windows this creates an undeletable file. Use `> /dev/null` in Git Bash or simply omit redirection.
- NEVER create files named `nul`, `con`, `prn`, `aux`, `com1`-`com9`, or `lpt1`-`lpt9` — these are reserved Windows device names.

## Project Overview
Goldenstat är en Flask-baserad webbapplikation för dartstatistik. Visar statistik från Stockholmsserien, Riksserien och cupturneringar.

## Tech Stack
- **Backend**: Python 3.11, Flask, Flask-Caching (FileSystemCache)
- **Databaser**: SQLite - tre separata:
  - `goldenstat.db` - Stockholmsserien (ligamatcher)
  - `riksserien.db` - Riksserien (ligamatcher)
  - `cups.db` - Cupturneringar (eget schema, n01 API-data)
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Scraping**: Playwright (ligamatcher från nakka.com), Requests (cuper via n01 API)
- **Deploy**: Railway med Gunicorn
- **CI/CD**: GitHub Actions (daglig ligaimport 02:00 UTC, nattlig cupimport 04:00 UTC)

## Project Structure
```
goldenstat/
├── app.py                          # Flask-app, config, delade helpers (~200 rader)
├── database.py                     # DartDatabase (goldenstat.db / riksserien.db)
├── cup_database.py                 # CupDatabase (cups.db)
├── routes/
│   ├── league.py                   # Index, divisioner, top-stats, weekly-stats
│   ├── players.py                  # Spelarsök, spelarstatistik, kastdata
│   ├── matches.py                  # Submatch, matchdetaljer, seriematcher
│   ├── teams.py                    # Lag, lineup, dubbel, klubbar
│   ├── tournaments.py              # Cupspel (cups.db, fristående)
│   └── tracking.py                 # Analytics-endpoints
├── templates/
│   ├── base.html                   # Bas-template med navigation
│   ├── index.html                  # Huvudsida
│   ├── tournaments.html            # Cupspel
│   ├── series_matches.html         # Seriematcher
│   ├── match_overview.html         # Matchöversikt
│   └── sub_match_throws.html       # Kastöversikt
├── static/
│   ├── css/style.css               # Huvudstylesheet
│   └── js/app.js                   # Frontend JavaScript
├── daily_import.py                 # Daglig ligaimport (GitHub Actions)
├── nightly_cup_import.py           # Nattlig cupimport (GitHub Actions)
├── import_cup.py                   # CupImporter-klass
├── smart_season_importer.py        # Smart ligaimport med spelarmappningar
├── cache_warmup.py                 # Cache warmup (weekly-stats + top-stats, båda ligorna)
├── gunicorn.conf.py                # Gunicorn-config för produktion
└── .github/workflows/
    ├── daily-import.yml            # 02:00 UTC - ligamatcher
    ├── nightly-cup-import.yml      # 04:00 UTC - cuper
    └── pr-checks.yml               # Lint + import-test
```

## Architecture
- `app.py` registrerar 6 Flask Blueprints och innehåller delade helpers
- Delade helpers: `get_current_db()`, `get_current_db_path()`, `get_effective_sub_match_query()`, `get_effective_player_ids()`, `parse_match_position()`
- Liga väljs via `?league=riksserien` query parameter
- Cupstatistik har egna routes under `/tournaments` med separat databas
- Cache warmup förpopulerar weekly-stats och top-stats för båda ligorna vid start

## Development Environment
- **Python**: 3.11
- **Lokal server**: `python app.py` → http://localhost:3000
- **Skippa warmup**: `python app.py --no-warmup`
- **Version Control**: Git med GitHub
- **Linting**: flake8

## Common Workflows
1. **Starta dev-server**:
   ```bash
   python app.py --no-warmup
   ```

2. **Importera en cup manuellt**:
   ```bash
   python import_cup.py <tdid>
   ```

3. **Testa nattlig cupimport (dry run)**:
   ```bash
   python nightly_cup_import.py --dry
   ```

4. **Daglig ligaimport**:
   ```bash
   python daily_import.py
   ```

## Key Features
- Spelarsök och detaljerad spelarstatistik
- Lagsidor med lineup och dubbelpar
- Topplistor (all-time och per säsong)
- Veckans prestationer
- Seriematcher per vecka/division
- Matchdetaljer med kastöversikt
- Cupturneringsstatistik (gruppspel, slutspel, kastdetaljer)
- Stöd för två ligor (Stockholmsserien, Riksserien)

## Notes
- Tre separata SQLite-databaser med olika scheman
- Cups.db har egna `players`, `legs`, `throws`-tabeller (ingen delad data med ligadatabaserna)
- `nightly_cup_import.py` har `SKIP_TDIDS` för turneringar som inte ska importeras
- `import_cup.py` hanterar namnuppdelning av dubbelpar (separator: &, /, +, och)
