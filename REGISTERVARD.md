# Registervård — Goldenstat

## Översikt

Databaserna lagras som **GitHub Release-assets** i releasen `db-latest`, inte i git:

| Databas | Innehåll | Uppdateras av |
|---|---|---|
| `goldenstat.db` | Seriematcher (Stockholmsserien) | `daily_import.py` varje natt |
| `cups.db` | Cuper från n01 | `nightly_cup_import.py` varje natt, `cup_backlog_import.py` manuellt |
| `riksserien.db` | Riksserien | Ingen automatisk import, hämtas och laddas upp oförändrad |
| `sommarserien.db` | Sommarserien 2026 | Avslutad, importen är avstängd |

Varje körning hämtar databaserna från releasen, ändrar dem och laddar upp dem igen.
Railway bygger om sajten när något pushas till `main` och hämtar då databaserna från
releasen. Dockerfilen kontrollerar att varje fil är hel (`check_database.py`) och
stoppar bygget om den inte är det, så att den förra deployen ligger kvar.

**Ändringar som görs direkt i en databas lokalt skrivs över av nästa körning.** Allt som
ska vara kvar sparas som en SQL-migrering i repot.

## Workflows

Alla tre ligger i samma concurrency-grupp (`db-release`). En körning väntar på att den
som pågår blir klar, så att de inte skriver över varandras databaser. GitHub håller bara
en väntande körning per grupp, och en ny väntande körning avbryter den som väntade före.
Starta därför inte flera saker samtidigt, och avbryt aldrig en körning under steget som
laddar upp databaserna.

### Daily Database Import (`daily-import.yml`)

Körs varje natt 00:23 UTC.

1. Hämtar databaserna och kör nya migreringar.
2. `daily_import.py` importerar seriematcher till `goldenstat.db`.
3. `nightly_cup_import.py` importerar nya cuper till `cups.db`:
   - alla färdigspelade turneringar i ligorna i `LEAGUES`, oavsett ålder
   - titelsökningar i `SEARCHES`, men bara cuper som spelats de senaste
     `RECENT_DAYS` (21) dagarna
   - turneringarna i `EXTRA_TDIDS`
   - cuper med färre än 12 spelare noteras i `cup_skipped` och söks inte igen
4. Laddar upp alla databaser och committar importloggen. Det är den pushen som får
   Railway att deploya.

### DB Maintenance (`db-maintenance.yml`)

Rena databasuppdateringar utan import. Körs automatiskt när något under `migrations/`
mergas till `main`, och kan startas manuellt med ett skript att köra efter
migreringarna, t.ex. `fix_player_averages.py`.

- Bara de databaser som faktiskt ändrats laddas upp.
- **Torrkörning:** startas den från en annan gren än `main` (eller med `dry_run`
  ikryssat) laddas inget upp. De ändrade databaserna sparas i stället som artefakt i
  tre dagar. Så provas en ny migrering mot de riktiga databaserna innan den mergas.
- En logg sparas i `import_logs/db_maintenance_*.json`.

### Cup Backlog Import (`cup-backlog.yml`)

Manuell. Importerar äldre cuper från kön i tabellen `cup_backlog`, nyaste först, tills
tidsgränsen (`minutes`, standard 300) är slut. Det som inte hinns med ligger kvar till
nästa körning.

Med `search` ikryssat söker den först igenom alla titelsökningar tillbaka till
`SEARCH_SINCE` (2023-11-01) och lägger det som saknas i kön. Det fångar cuper som
nattjobbet missar: sådana som blivit färdigmarkerade mer än 21 dagar efter speldagen,
eller som spelades medan nattjobbet låg nere.

## SQL-migreringar

`apply_migrations.py` håller reda på körda filer i tabellen `_migrations`. Varje fil körs
exakt en gång per databas, så det är ofarligt att köra skriptet flera gånger.

```bash
python apply_migrations.py goldenstat.db migrations/goldenstat
python apply_migrations.py cups.db migrations/cups
python apply_migrations.py sommarserien.db migrations/sommarserien
```

### Skapa en migrering

1. Lägg en ny fil i rätt katalog med nästa löpnummer, t.ex.
   `migrations/cups/010_beskrivning.sql`.
2. Skriv SQL:en så att den tål att databasen inte ser ut som väntat:
   - `INSERT OR IGNORE`, `IF NOT EXISTS`
   - vakta varje rad med både id och namn, t.ex.
     `WHERE EXISTS (SELECT 1 FROM players WHERE id = 2356 AND name = 'Alexander Kallin')`,
     så att inget händer om id:t hunnit betyda något annat
3. Prova lokalt mot en nedladdad kopia:
   ```bash
   gh release download db-latest --pattern "cups.db" --clobber
   python apply_migrations.py cups.db migrations/cups
   ```
4. Pusha grenen och kör **DB Maintenance** från grenen. Det blir en torrkörning, och
   artefakten visar resultatet mot de riktiga databaserna.
5. Merga. DB Maintenance kör då migreringen på `main`, laddar upp och Railway deployar.

Kör inte `gh release upload` för hand. En lokal databas kan vara inaktuell, och en
uppladdning medan en workflow kör skrivs över eller skriver över dess ändringar.

## Spelarmappningar: seriematcher och cuper

Serie- och cupdatabaserna löser dubbletter och felstavningar på helt olika sätt. En
sammanslagning som är rätt för den ena fungerar inte i den andra.

### Skillnaderna i korthet

| | Seriematcher (`goldenstat.db`) | Cuper (`cups.db`) |
|---|---|---|
| Tabeller | `player_aliases` (hel spelare) och `sub_match_player_mappings` (per delmatch) | `cup_player_mappings` (hel spelare) |
| Klubbkontext | Ja, varje spelare spelar för ett lag | Nej, cuper har inga lag |
| Samma namn, olika personer | Går att skilja åt med klubben i namnet, t.ex. "Mats Andersson (AIK Dart)" | Går inte att skilja åt, blir samma spelare |
| Hur importen matchar namn | Smart matchning: exakt namn, versaler, förnamn + klubb, klubbvarianter, bindestreck | Bara exakt normaliserat namn |
| Skapar importen mappningar själv? | Ja | Nej, aldrig |
| Ny felstavning vid import | Fångas ofta automatiskt | Blir alltid en ny spelare |
| Läser sajten mappningstabellen? | Ja, `sub_match_player_mappings` vid varje fråga. `player_aliases` läses inte av sajten | Delvis, alla frågor gör det inte |
| Vad en sammanslagning måste flytta | Delmatchdeltagare och delmatchmappningar till den kvarvarande spelaren | Kopplingarna i `participant_players` till den kvarvarande spelaren |
| Verktyg för att hitta kandidater | Inget färdigt | `find_cup_typos.py`, `review_typos.py` |

### Seriematcher

**Import.** `SmartSeasonImporter` använder `SmartPlayerMatcher`
(`smart_import_handler.py`), som försöker hitta en befintlig spelare på flera sätt:
exakt namn, skillnad i versaler, förnamn tillsammans med klubb, varianter av
klubbnamnet och bindestreck/mellanslag. Ett ensamt förnamn utan säker träff blir en
egen spelare med klubben i namnet, t.ex. "Kari (Tyresö DC)". Finns namnet redan men
matchningen är osäker, t.ex. för att spelaren hör till en annan klubb, får den nya
spelaren också klubben i namnet.

Efter matchningen kollar `resolve_player_alias`:

- Finns spelaren i `player_aliases` används den kanoniska spelaren, och en rad
  skrivs i `sub_match_player_mappings` ("Auto via player_aliases").
- Annars, om spelaren tidigare mappats till samma person minst två gånger i samma
  klubb (confidence ≥ 90) och inte har några omappade matcher, mappas den automatiskt
  dit igen ("Auto via historical sub_match_player_mappings").

**Sajten** slår upp spelare på namn och läser `sub_match_player_mappings` i varje
fråga: en delmatch med mappning räknas för `correct_player_name`, inte för den
ursprungliga spelaren. `player_aliases` läses bara av importen.

**Två sorters rättelser:**

- *Samma person under flera id:n* (felstavning, accenter, dubbelregistrering): lägg
  till rader i `player_aliases` och flytta allt till den kvarvarande spelaren. Se
  `027_merge_duplicate_players.sql`. Slutet av den filen gör flytten och kan kopieras:
  det pekar om kedjor av alias, tar bort delmatchmappningar mellan två id:n för samma
  spelare, flyttar mappningar och flyttar `sub_match_participants`.
- *Ett id som täcker flera personer*: dela upp per delmatch, antingen med
  `sub_match_player_mappings` (se `002_bernte_bernth_mapping.sql`) eller genom att
  flytta deltagarna i en viss klubb till ett eget id och sätta klubben i namnet (se
  `028_merge_reviewed_duplicates.sql`).

Samma namn i två klubbar samma säsong är ofta två personer. Granska de fallen för hand.

### Cuper

**Import.** `CupDatabase.get_or_create_player` (`cup_database.py`) normaliserar namnet
(versaler, klubb efter ett fullständigt namn tas bort, "Linus Dellby (Bålsta Dart
Club)" blir "Linus Dellby"; ett ensamt förnamn behåller klubben, "Micke (hdc)") och
letar sedan bara efter exakt samma namn. Är den spelaren ett alias i
`cup_player_mappings` används den kanoniska spelaren, men bara ett steg.

Det betyder:

- En stavning som redan kopplats ihop hamnar rätt i alla framtida cuper. Inget
  behöver köras om.
- En stavning som aldrig setts förut blir en ny spelare. Importen gissar aldrig.
- Gamla cuper har fler varianter än nya. Efter större backlog-körningar dyker det upp
  nya kandidater.

**Sajten** döljer alias i spelarlistan, samlar kanonisk spelare och alias på
spelarsidan och visar `canonical_name` i matchlistor. Andra frågor går direkt på
`participant_players`, så en sammanslagning måste också flytta kopplingarna dit.

**Kedjor.** Eftersom bara ett steg följs måste varje alias peka direkt på den slutliga
spelaren, aldrig på ett annat alias.

**En sammanslagning** (se `009_merge_reviewed_typos.sql`) består av:

1. En vaktad `INSERT OR IGNORE INTO cup_player_mappings` per par, med `mapping_reason`
   satt till t.ex. `typo` eller `name_variant`.
2. Den generiska avslutningen från 008/009, som kan kopieras rakt av: platta ut kedjor,
   synka `canonical_name` mot spelarens nuvarande namn, ta bort dubbla kopplingar och
   flytta kopplingarna i `participant_players` från alias till kanonisk spelare.

## Arbetsgång för namnsammanslagning

### Cuper

1. Hämta den senaste `cups.db`:
   ```bash
   gh release download db-latest --pattern "cups.db" --clobber
   ```
2. Ta fram kandidater. Fynden kräver ett exakt lika namnled och högst två tecken skillnad
   i resten:
   ```bash
   python find_cup_typos.py
   python review_typos.py --dry
   ```
   Kör inte `review_typos.py` utan `--dry` om resultatet ska vara kvar. Den skriver
   direkt i den lokala databasen, och det försvinner vid nästa körning.
3. Granska. Lämna vanliga namn som skiljer sig på en bokstav (Jonsson/Jansson,
   Lund/Lundh) om det inte finns stöd för att det är samma person. Välj den stavning
   som de flesta matcherna har som kvarvarande namn.
4. Skriv de godkända paren som en ny migrering enligt mönstret i 009 och följ stegen
   under [Skapa en migrering](#skapa-en-migrering).

### Seriematcher

Det finns inget färdigt verktyg. Ta fram kandidater med frågor mot `goldenstat.db`
(samma namn på flera id:n, namn som bara skiljer sig i accenter, bindestreck eller
versaler) och skriv migreringen enligt mönstret i 027 eller 028. Testerna i
`tests/test_league_player_merge.py` visar vad avslutningen ska åstadkomma.

## Tabeller

### player_aliases (goldenstat.db)

```sql
CREATE TABLE player_aliases (
    alias_player_id INTEGER PRIMARY KEY,      -- Spelar-ID som är ett alias
    canonical_player_id INTEGER NOT NULL,     -- Rätt spelare att peka på
    canonical_player_name TEXT NOT NULL,      -- Namn på rätt spelare
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);
```

### sub_match_player_mappings (goldenstat.db, sommarserien.db)

```sql
-- En rad per delmatch och spelare:
--   sub_match_id, original_player_id, correct_player_id, correct_player_name,
--   confidence (1-100), mapping_reason, notes
-- UNIQUE(sub_match_id, original_player_id), original_player_id != correct_player_id
```

### cup_player_mappings (cups.db)

Skapas av `cup_database.py`.

```sql
CREATE TABLE cup_player_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias_player_id INTEGER NOT NULL UNIQUE,  -- Bara en kanonisk spelare per alias
    canonical_player_id INTEGER NOT NULL,
    alias_name TEXT NOT NULL,
    canonical_name TEXT NOT NULL,             -- Visas i matchlistor
    mapping_reason TEXT,                      -- t.ex. 'typo', 'name_variant'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK(alias_player_id != canonical_player_id)
);
```
