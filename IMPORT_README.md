# GoldenStat Import System

Detta system importerar matchdata från N01 Darts API för säsongen 2025/2026.

## Översikt

Systemet består av tre huvudkomponenter:
1. **URL Generator** - Genererar alla möjliga match-URLs för en division
2. **Season Importer** - Importerar matchdata från URL-lista
3. **Division Script** - Kombinerar båda stegen i ett enkelt kommando

## Användning

### Snabb import av en division
```bash
./import_division.sh t_jM8s_0341
```

### Manuella steg

#### Steg 1: Generera match-URLs
```bash
python3 generate_match_urls.py t_jM8s_0341
```
Detta skapar filen `t_jM8s_0341_match_urls.txt` med alla 110 möjliga match-URLs.

#### Steg 2: Importera matcher
```bash
python3 new_season_importer.py t_jM8s_0341 t_jM8s_0341_match_urls.txt
```

### Alternativt: Generera URLs automatiskt
```bash
python3 new_season_importer.py t_jM8s_0341
```
Detta genererar URLs automatiskt utan att spara till fil.

## Filstruktur

### generate_match_urls.py
- Hämtar spelschema från N01 API
- Identifierar alla schemalagda matcher (55 st för division 2A)
- Genererar 2 URL-varianter per match (110 totalt)
- Sparar URLs till fil med metadata

### new_season_importer.py
- Läser URLs från fil eller genererar dem dynamiskt
- Testar varje URL för att hitta spelade matcher
- Importerar fullständig matchdata inkl. sub-matcher, spelare, legs och kast
- Sparar allt i SQLite-databasen

### import_division.sh
- Kombinerar båda stegen
- Återanvänder URL-fil om den är mindre än 1 dag gammal
- Ger tydlig progress-information

## API-endpoints

Systemet använder dessa N01 Darts API-endpoints:

1. **Spelschema**: `POST https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_tournament.php?cmd=get_lg_schedule`
   - Body: `{"tdid":"t_jM8s_0341","div":0}`
   - Returnerar alla schemalagda matcher med lag-par och round-koder

2. **Matchdata**: `GET https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_online_t.php?cmd=get_setdata&tmid={match_id}`
   - Returnerar komplett matchdata om matchen har spelats
   - Returnerar tom array om matchen inte har spelats

## URL-format

Match-URLs följer detta format:
```
https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_online_t.php?cmd=get_setdata&tmid={tdid}_lg_0_{round_code}_{team1}_{team2}
```

Exempel:
- `t_jM8s_0341_lg_0_mljp_ozmn_rTNf` = Division t_jM8s_0341, round mljp, Engelbrekt vs Dartanjang

## Exempel på lyckad import

För division `t_jM8s_0341` (Division 2A) importerades 5 spelade matcher:

1. **Faster Annas (2A) vs AIK Dart (2A)** - 20-35
2. **Cobra DC (2A) vs Backen (2A)** - 25-30
3. **Dartbiten (2A) vs Mjölner (2A)** - 38-7
4. **Dartanjang (2A) vs Engelbrekt (2A)** - 35-20
5. **Rockhangers DC (2A) vs 181 DC (2A)** - 8-37

## Fördelar med detta system

1. **Effektivt**: Använder riktiga lag-par från spelschema istället för alla kombinationer
2. **Cachebar**: URL-filer kan återanvändas tills nya matcher läggs till
3. **Robust**: Hanterar både filbaserade och dynamiska URL-generering
4. **Komplett**: Importerar all matchdata inklusive individuella kast
5. **Skalbart**: Kan enkelt användas för flera divisioner

## Tekniska detaljer

- **Databas**: SQLite med tabeller för matches, teams, players, sub_matches, legs, throws
- **Error handling**: Graceful hantering av 404/tomma svar från API
- **Rate limiting**: 1 sekunds delay mellan requests
- **Encoding**: UTF-8 stöd för svenska tecken
- **Logging**: Detaljerad progress-information med emojis för tydlighet