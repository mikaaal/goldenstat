# Arkiverade filer

Denna mapp innehåller gamla script och verktyg som inte längre används aktivt i produktionen, men som kan vara användbara för framtida referens.

## Mappstruktur

### `debug_scripts/`
Test- och debugscript som användes under utvecklingen:
- `test_*.py` - Testscript
- `debug_*.py` - Debugverktyg
- `check_*.py` - Verifieringsscript
- `verify_*.py` - Valideringsscript

### `fixes/`
Engångs-fixar och analysverktyg:
- `fix_*.py` - Script för att fixa specifika problem (t.ex. dubbletter, stavfel)
- `cleanup_*.py` - Script för att städa upp data
- `analyze_*.py` - Analysverktyg
- `find_*.py` - Verktyg för att hitta problem
- `detect_*.py` - Detekteringsverktyg
- `merge_*.py` - Sammanslagningsverktyg

### `player_mapping_tools/`
Alla verktyg som användes för att mappa spelares olika namnvarianter:
- Automatiska mappningsverktyg
- Manuella mappningsscript för specifika spelare
- Analysverktyg för att hitta dubbletter

**OBS:** Dessa verktyg är inte längre nödvändiga eftersom all mappning nu finns i `sub_match_player_mappings` tabellen i databasen.

### `old_importers/`
Gamla importscript som ersatts av nyare versioner:
- `import_season.py`
- `multi_league_importer.py`
- `run_full_import.py`
- etc.

**Nuvarande importers:**
- `daily_import.py` - Daglig import
- `new_season_importer.py` - Ny säsong
- `smart_season_importer.py` - Smart import med mappningar
- `single_file_import.py` - Importera enskilda filer

### `match_urls/`
Gamla match URL-filer från tidigare säsonger och importer.

**Nuvarande match URLs:** finns i `/current_match_urls/`

### `data_files/`
Gamla JSON- och textfiler med testdata och exporterad data.

### `docs/`
Gammal dokumentation, SQL-scheman, Docker-konfiguration etc.

---

## När ska jag använda arkiverade filer?

**Använd INTE** dessa filer i normal drift.

**Använd** om du behöver:
- Förstå hur ett gammalt problem löstes
- Återanvända logik från ett gammalt script
- Debugga ett historiskt problem
- Förstå hur mappningsystemet byggdes upp

---

*Arkiverat: 2025-10-05*
