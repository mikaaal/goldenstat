# Goldenstat - Darttävlingsstatistik

En webbapplikation för att visa och analysera statistik från Stockholmsseriens darttävlingar.

## Projektstruktur

```
goldenstat/
├── app.py                      # Flask-server (huvudapplikation)
├── database.py                 # Databashantering
├── goldenstat.db              # SQLite-databas
├── requirements.txt           # Python-dependencies
├── cookies.txt               # Nakka-inloggning
│
├── Import-system:
├── daily_import.py           # Daglig import av nya matcher
├── new_season_importer.py    # Import av nya säsonger
├── smart_season_importer.py  # Smart import med spelarmappningar
├── smart_import_handler.py   # Smart player matching (används av importers)
├── single_file_import.py     # Import av enskilda filer
├── generate_match_urls.py    # Generera match-URLer för import
│
├── Underhåll:
├── fix_player_averages.py    # Fixa pilsnitt-beräkningar
│
├── Frontend:
├── static/                   # CSS, JavaScript
│   ├── css/style.css
│   └── js/app.js
├── templates/                # HTML-templates
│   ├── index.html           # Huvudsida
│   └── sub_match_throws.html # Kastöversikt
│
├── Data:
├── current_match_urls/       # Match-URLer för aktuell säsong
├── import_logs/             # Importloggar
│
└── archive/                 # Arkiverade script (ej aktiva)
    ├── debug_scripts/       # Test- och debugscript
    ├── fixes/              # Engångs-fixar
    ├── player_mapping_tools/ # Gamla mappningsverktyg
    ├── old_importers/      # Ersatta importers
    ├── match_urls/         # Gamla match-URLer
    ├── data_files/         # Testdata
    └── docs/               # Gammal dokumentation
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

3. Öppna webbläsaren på: `http://localhost:3000`

## Import av data

### Daglig import (uppdatera med nya matcher)
```bash
python daily_import.py
```

### Import av ny säsong
```bash
python new_season_importer.py
```

### Import med spelarmappningar (smart)
```bash
python smart_season_importer.py
```

## Viktiga funktioner

- **Spelarsök**: Sök och visa statistik för enskilda spelare
- **Lagsidor**: Se alla spelare i ett lag och deras statistik
- **Topplista**: Rankning baserad på pilsnitt i singelmatcher
- **Matchdetaljer**: Visa alla kast i en match
- **Spelarmappning**: Automatisk hantering av olika namnvarianter för samma spelare

## Teknisk stack

- **Backend**: Python, Flask
- **Databas**: SQLite
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Data**: Importeras från nakka.com (Dartconnect)

## Underhåll

### Fixa pilsnitt-beräkningar
Om pilsnitt behöver räknas om (t.ex. efter datafix):
```bash
python fix_player_averages.py
```

### Loggar
Importloggar sparas i `import_logs/` med timestamp och detaljer om vad som importerades.

## Arkiverade filer

Gamla script och verktyg finns i `archive/`-mappen. Se `archive/README.md` för mer information.

**OBS:** Använd INTE arkiverade filer i produktion.

---

*Senast uppdaterad: 2025-10-05*
