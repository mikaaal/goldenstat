# Registervård — Goldenstat

## Översikt

Databaserna (`goldenstat.db`, `cups.db`, `riksserien.db`) lagras som **GitHub Release-assets** (release `db-latest`), inte i git. De laddas ned i början av varje CI-körning och laddas upp igen efteråt.

Manuella ändringar (spelarmappningar, aliases) som görs lokalt mot en databas förloras vid nästa dagliga import — om de inte sparas som **SQL-migreringar** i repot.

## Daglig import-pipeline

```
┌─ GitHub Actions (daily-import.yml) ─────────────────────┐
│                                                          │
│  1. Checkout repo                                        │
│  2. Ladda ned databaser från release db-latest           │
│  3. Applicera SQL-migreringar (apply_migrations.py)      │
│  4. Kör daily_import.py (liga-matcher)                   │
│  5. Kör nightly_cup_import.py (cup-matcher)              │
│  6. Ladda upp databaser till release db-latest           │
│  7. Committa importloggar                                │
└──────────────────────────────────────────────────────────┘
```

## SQL-migreringar

### Hur det fungerar

`apply_migrations.py` skapar en `_migrations`-tabell i databasen som spårar vilka migreringar som redan körts. Varje .sql-fil körs exakt en gång — det är säkert att köra scriptet upprepade gånger.

```bash
python apply_migrations.py goldenstat.db migrations/goldenstat
python apply_migrations.py cups.db migrations/cups
```

### Hur man skapar en ny migrering

1. Skapa en ny SQL-fil i rätt katalog:
   - `migrations/goldenstat/` — för goldenstat.db
   - `migrations/cups/` — för cups.db

2. Namnge filen med löpnummer: `004_beskrivning.sql`

3. Skriv SQL:en. Använd `IF NOT EXISTS` / `INSERT OR IGNORE` / `WHERE EXISTS` för idempotens.

4. Testa lokalt:
   ```bash
   python apply_migrations.py goldenstat.db migrations/goldenstat
   ```

5. Committa och pusha — migreringen körs automatiskt vid nästa dagliga import.

### Filstruktur

```
migrations/
├── goldenstat/
│   ├── 001_player_aliases_table.sql    — Skapar player_aliases-tabell + initiala aliases
│   ├── 002_bernte_bernth_mapping.sql   — Bernte → Bernth Andersson mappningar
│   └── 003_kari_dagudde_mapping.sql    — Kari-varianter → Kari Dagudde mappningar
└── cups/
    └── 001_placeholder.sql             — Placeholder (cup_player_mappings skapas i cup_database.py)
```

## Registervård lokalt

### Steg-för-steg

1. **Hämta senaste databaserna:**
   ```bash
   gh release download db-latest --pattern "*.db" --clobber
   ```

2. **Gör ändringar** — antingen direkt i SQLite eller genom att skapa en ny migreringsfil.

3. **Om du skapar en migrering:** testa den lokalt, committa SQL-filen, pusha.

4. **Om du gör ad-hoc ändringar direkt i databasen:** ladda upp manuellt:
   ```bash
   gh release upload db-latest goldenstat.db cups.db --clobber
   ```
   OBS: Ad-hoc ändringar kan skrivas över av nästa dagliga import. Föredra migreringar.

## Tabeller för registervård

### player_aliases (goldenstat.db)

Mappar alias-spelare till kanoniska spelare. Används automatiskt av `smart_season_importer.py` vid import — när en spelare identifieras som ett alias, skapas en mappning och den kanoniska spelaren används istället.

```sql
CREATE TABLE player_aliases (
    alias_player_id INTEGER PRIMARY KEY,     -- Spelar-ID som är ett alias
    canonical_player_id INTEGER NOT NULL,     -- Rätt spelare att peka på
    canonical_player_name TEXT NOT NULL,      -- Namn på rätt spelare
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);
```

**Exempel:** Spelare "Kari (Tyresö DC)" (id 2182) är ett alias för "Kari Dagudde" (id 2677).

### sub_match_player_mappings (goldenstat.db)

Per-submatch mappning från en felaktigt tilldelad spelare till den rätta. Används av webbappen för att visa rätt statistik.

```sql
-- Kolumner: sub_match_id, original_player_id, correct_player_id,
--           correct_player_name, confidence, mapping_reason, notes
```

### cup_player_mappings (cups.db)

Samma koncept som player_aliases men för cup-databasen. Skapas automatiskt av `cup_database.py`.

```sql
CREATE TABLE cup_player_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias_player_id INTEGER NOT NULL UNIQUE,
    canonical_player_id INTEGER NOT NULL,
    canonical_player_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);
```
