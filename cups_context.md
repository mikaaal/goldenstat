# Cupspel - Importerkontext

## Bakgrund

[n01](n01darts.com) är en japansk dartplattform som används för att spela och registrera dartmatcher online. Lokala dartklubbar i Stockholm (bl.a. SoFo House och East Dart) använder n01:s turneringsfunktion för sina cuper.

Turneringarna visas i webbläsaren på:
```
https://n01darts.com/n01/tournament/comp.php?id={tdid}
```

All turneringsdata finns tillgänglig via n01:s JSON-API på:
```
https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/
```

`cup_database.py` och `import_cup.py` hämtar data från detta API och sparar till en lokal SQLite-databas (`cups.db`). Denna databas är **separat** från projektets huvuddatabas `goldenstat.db` och `riksserien.db` som innehåller ligamatcher (Stockholmsserien, Riksserien). De tre databaserna delar ingen data och har olika scheman - `cups.db` har egna `players`-, `legs`- och `throws`-tabeller. Däremot samlas allt i en app där användaren kan välja att titta på statistik från Stockholmsserien eller Riksserien. Nu ska även olika cuper bli tillgängliga.

## Ordlista

| Term | Betydelse |
|------|-----------|
| `tdid` | Tournament ID. Unikt ID för en hel turnering, t.ex. `t_ALIS_0219` |
| `tpid` | Tournament Participant ID. Unikt ID för en deltagare inom en turnering, t.ex. `aal3` |
| `tmid` | Tournament Match ID. Konstruerat ID för en specifik match, t.ex. `t_7zbm_0674_rr_0_aal3_jAq2` |
| `rr` | Round-robin. Gruppspelsfasen där alla möter alla |
| `t` | Tournament. Huvudslutspelet (knockout/utslagning) |
| `s2` | Secondary tournament. B-slutspelet för de som inte kvalificerade sig till huvudslutspelet |
| `leg` | Ett enskilt spel inom en match (t.ex. "först till 501 ner till 0") |
| `side` | Sida 1 eller 2 i en match. Kan vara en spelare (singel) eller ett par (dubbel) |
| `lgid` | League ID. Kopplar turneringar som tillhör samma liga/serie |

## Turneringsformat

En cup har tre faser som spelas i ordning:

1. **Round-robin (`rr`)** - Deltagarna delas in i grupper om 3-4. Alla möter alla inom gruppen. De bästa går vidare till huvudslutspel, resten till B-slutspel.
2. **Knockout (`t`)** - Utslagsformat. Förloraren åker ut. Bracket med byes om antalet inte är jämn tvåpotens.
3. **B-knockout (`s2`)** - Samma format som knockout, men för de som inte kvalificerade sig från gruppspelet.

Varje fas har sin egen inställning för antal legs per match (`limit_leg_count`), och kan även ha specialregler per runda via `game_setting` (t.ex. fler legs i final).

## Skillnader mellan klubbar

| | SoFo House | East Dart |
|--|-----------|-----------|
| Namnformat | Normal case: `Kevin Doets` | VERSALER: `KEVIN DOETS` |
| Gruppstorlek | 3 spelare | 3-4 spelare |
| Startpoäng | 501 (singel) eller handicap (dubbel) | 501 eller 301 (double-in) |
| Dubbelcup | Ja, namn med " & ", individuell `startScore` | Nej (hittills bara singel) |
| Klubbtillhörighet i namn | Nej | Ibland, t.ex. `DANIEL LARSSON (SSDC)` |
| Extra knockout-resultat | Nej | Ja, play-in-matcher utanför bracket |

## Kända turneringar

### SoFo House Poängsamlarcup
| tdid | Typ | Beskrivning | API-data |
|------|-----|-------------|----------|
| `t_ALIS_0219` | Dubbel, handicap | startScore per par (530-670), 21 par | [JSON](https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_tournament.php?cmd=get_data&tdid=t_ALIS_0219) |
| `t_7zbm_0674` | Singel, 501 | 45 deltagare, 15 grupper om 3 | [JSON](https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_tournament.php?cmd=get_data&tdid=t_7zbm_0674) |

### East Cup
| tdid | Typ | Beskrivning | API-data |
|------|-----|-------------|----------|
| `t_cOBD_2552` | Singel, 501 | 38 deltagare, 10 grupper om 3-4 | [JSON](https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_tournament.php?cmd=get_data&tdid=t_cOBD_2552) |
| `t_fR8b_7492` | Singel, **301 double-in** | 26 deltagare, 7 grupper | [JSON](https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_tournament.php?cmd=get_data&tdid=t_fR8b_7492) |
| `t_2xO7_7499` | Singel, 501 | 45 deltagare, 12 grupper | [JSON](https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_tournament.php?cmd=get_data&tdid=t_2xO7_7499) |

## API

Bas-URL: `https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/`

### Turneringsdata
```
GET {bas}/n01_tournament.php?cmd=get_data&tdid={tdid}
```
Returnerar all turneringsinfo i ett enda JSON-objekt: metadata, entry_list, rr_table, rr_result, t_table, t_result, s2_table, s2_result.

### Detaljerad matchdata (legs/throws)
```
GET {bas}/n01_online_t.php?cmd=get_setdata&tmid={tmid}
```
Returnerar en JSON-array med legData och statsData för en specifik match. Returnerar `[]` om matchid:t inte finns.

tmid-format: `{tdid}_{phase}_{index}_{tpid1}_{tpid2}`

Exempel:
- `t_7zbm_0674_rr_0_aal3_jAq2` (round-robin grupp 0)
- `t_7zbm_0674_t_0_bFk4_o4lT` (knockout runda 0)
- `t_ALIS_0219_s2_1_uKgs_vdO9` (B-slutspel runda 1)

Bara en riktning av tpid-paret returnerar data. Den andra ger `[]`. Importern testar omvänd ordning som fallback.

## Importflöde

`python import_cup.py <tdid>` kör följande steg:

1. **Hämta turneringsdata** - GET `get_data` → spara till `tournaments`
2. **Processa entry_list** - Varje entry → `participants`-rad. Namn parsas:
   - Om " & " finns i namnet → splitta till två `players` (dubbelpar)
   - Annars → en `player`
   - Länka via `participant_players`
3. **Processa resultat från alla tre faser:**
   - **rr**: Iterera grupper, skapa match per riktning (A→B, B→A)
   - **t**: Para ihop konsekutiva entries i varje runda, hoppa över byes
   - **s2**: Samma som t
4. **Hämta detaljdata** - För varje match med `has_detail=0`:
   - GET `get_setdata` med tmid
   - Om `[]` → testa omvänd tpid-ordning
   - Parsa legData → `legs` + `throws`
   - `time.sleep(0.5)` mellan anrop
5. **Logga** - Skriv sammanfattning till `import_logs/cup_{tdid}_{timestamp}.json`

## Databasschema (cups.db)

### tournaments
Huvudtabell. En rad per cup.
- `tdid` (UNIQUE) - n01:s turnerings-ID
- `title` - Turneringens namn
- `tournament_date` - Datum
- `status` - n01-status (40 = avslutad)
- `team_games` - 0=singel, 1=dubbel (alltid 0 i praktiken, dubbel kan identifieras via " & " i namn men det kan även vara andra avskiljare)
- `lgid` - Liga-ID (kopplar cuper i samma serie)
- `start_score` - Default startpoäng (501 eller 301)

### participants
En rad per deltagare i en turnering. Kan vara en spelare (singel) eller ett par (dubbel).
- `tournament_id` → tournaments
- `tpid` - n01:s deltagarid, unikt inom turneringen
- `name` - Deltagarnamn som det står i n01 (oparserat)
- `start_score` - Individuell handicap-startpoäng (NULL = turneringens default)

### players
Global spelartabell. Namn normaliseras vid insättning.
- `name` - Normaliserat spelarnamn

### participant_players
Koppling deltagare ↔ spelare. En singel-deltagare har en spelare, ett dubbelpar har två.
- `participant_id` → participants
- `player_id` → players

### cup_matches
En rad per match. Fas + detalj beskriver var i turneringen matchen skedde.
- `tournament_id` → tournaments
- `phase` - `'rr'`, `'t'`, eller `'s2'`
- `phase_detail` - Gruppindex (rr) eller rundindex (t/s2)
- `participant1_id`, `participant2_id` → participants
- `p1_legs_won`, `p2_legs_won` - Resultat
- `p1_average`, `p2_average` - Snitt (tre-pilssnitt)
- `tmid` (UNIQUE per turnering) - Match-ID för API-anrop
- `has_detail` - 1 = legs/throws har hämtats

### legs
Ett leg inom en match.
- `cup_match_id` → cup_matches
- `leg_number` - 1-indexerat ordningsnummer
- `winner_side` - 1 eller 2
- `first_side` - Vilken sida som kastade först (1 eller 2)
- `total_rounds` - Antal kastomgångar

### throws
Enskilda kast (en omgång = 3 pilar om inte checkout).
- `leg_id` → legs
- `side_number` - 1 eller 2
- `round_number` - 1-indexerat
- `score` - Poäng den omgången
- `remaining_score` - Kvarvarande poäng efter kastet
- `darts_used` - Antal pilar (default 3, vid checkout = faktiskt antal)

### Index
```sql
idx_participants_tournament(tournament_id)
idx_participant_players_participant(participant_id)
idx_participant_players_player(player_id)
idx_cup_matches_tournament(tournament_id)
idx_cup_matches_phase(tournament_id, phase)
idx_legs_cup_match(cup_match_id)
idx_throws_leg(leg_id)
idx_players_name(name)
```

## API-datastruktur i detalj

### entry_list
```json
// Singel
{"tpid": "aal3", "name": "Kevin Doets", "c": ""}

// Dubbelpar med handicap
{"tpid": "d4PM", "name": "Masen & Pelle Christensen", "startScore": 670}

// Med klubbtillhörighet
{"tpid": "Xhky", "name": "DANIEL LARSSON (SSDC)"}

// Med smeknamn
{"tpid": "b4k2", "name": "PER-ERIK \"BACON\" BREDBERG"}
```

- `startScore` i entry_list = individuell handicap. Syns i legData som `left`-värdet i första throw-entry.
- `team_games` är `0` för alla kända cuper, även dubbelcuper. Dubbelpar identifieras via " & " i namn.
- `c` = land/klubb-flagga, inte relevant för import.

### rr_table / rr_result

Grupper kan ha 3 eller 4 spelare. Tomma platser = `""` i arrayen.

```json
// Grupp med 4
["HxIf", "mmEr", "JwPU", "Bk3x"]

// Grupp med 3 (tom fjärdeplats)
["euNT", "Gxh6", "r9V8", ""]
```

rr_result är indexerad per grupp. Varje deltagare har resultat mot alla motståndare:
```json
{
  "aal3": {
    "jAq2": {"r": 3, "a": 77.74},  // r = legs vunna, a = snitt
    "yCLE": {"r": 3, "a": 73.92}
  }
}
```

Båda riktningar finns i resultatet (A→B och B→A) men bara en riktning har detaljdata via API.

### t_table / s2_table (knockout)

Arrayindex = runda (0 = första, sista = vinnare).

```json
// Runda 0: paren paras ihop konsekutivt, "" = bye
["aal3", "", "bFk4", "o4lT", "9NzT", "gztg", ...]

// Sista elementet = bara vinnaren
["aal3"]
```

t_result/s2_result har färre entries än table (sista = bara vinnaren, ingen match). Hanteras av `if round_index >= len(results): continue`.

### Extra resultatposter i knockout

East-cuper kan ha extra resultat i en runda som inte motsvarar bracket-parningar (t.ex. play-in-matcher). Exempel från `t_cOBD_2552` s2_result[1]:
```json
"PFS5": {"zarp": {"r": 3}, "seM5": {"r": 0, "a": 35.44}}
```
PFS5 har resultat mot två motståndare i samma runda. Importern ignorerar dessa automatiskt eftersom den driver från table-parningar, inte resultat-nycklar.

### legData / playerData (throws)

```json
{
  "first": 0,           // 0-indexerad, vilken sida som kastar först
  "winner": 0,          // 0-indexerad, vilken sida som vann
  "currentRound": 7,    // totalt antal omgångar
  "playerData": [
    [  // Sida 1
      {"score": 0, "left": 501},     // Index 0: startposition, SKIPPA
      {"score": 60, "left": 441},    // Index 1: första kastet
      {"score": 100, "left": 341},
      ...
      {"score": -1, "left": 0}       // Negativt score = checkout
    ],
    [  // Sida 2
      {"score": 0, "left": 501},     // Index 0: startposition, SKIPPA
      {"score": 42, "left": 459},
      ...
    ]
  ]
}
```

**Startposition (index 0):** Alltid `score=0`. Skippas med `if round_index == 0 and score == 0`.

**Handicap:** Vid handicap-turneringar visar `left` i startpositionen det faktiska startvärdet (t.ex. 547, 591) istället för turneringens default (501).

**Checkout:** Negativt `score`-värde. `abs(score)` = antal pilar använda. `left=0`.
- `{"score": -1, "left": 0}` → 1 pil för checkout
- `{"score": -2, "left": 0}` → 2 pilar för checkout

**301 double-in:** Flera omgångar med `score=0, left=301` efter startpositionen = missade försök att kliva in (träffa dubbel). Dessa sparas som vanliga kast med `score=0, darts_used=3`. Skippas INTE - bara index 0 skippas.

**Förloraren:** Inga fler entries efter sista kastet (ingen checkout-rad).

## Namnhantering

East-cuper använder VERSALER: `"ALEXANDER FELLDIN"`, `"INGUS GRANDBERGS"`.
SoFo-cuper använder normal case: `"Kevin Doets"`, `"Noah Lind"`.

`CupDatabase.normalize_player_name()` normaliserar vid insättning i `players`-tabellen:

| Input | Output |
|-------|--------|
| `ALEXANDER FELLDIN` | `Alexander Felldin` |
| `PER-ERIK` | `Per-Erik` |
| `DANIEL LARSSON (SSDC)` | `Daniel Larsson (SSDC)` |
| `"BACON"` | `"Bacon"` |
| `TOMAS ÖBERG` | `Tomas Öberg` |
| `MIKA HAUTAMÄKI` | `Mika Hautamäki` |

Regler:
- Varje ord → `capitalize()` (title case)
- Bindestreck → varje del capitaliseras separat
- Parentesinnehåll bevaras som det är (klubbförkortningar)
- Citattecken → inre text capitaliseras

## Idempotens

- `tournaments.tdid` UNIQUE → skippar om redan finns
- `cup_matches(tournament_id, tmid)` UNIQUE → skippar redan importerade matcher
- `participants(tournament_id, tpid)` UNIQUE → skippar dubbletter
- `participant_players(participant_id, player_id)` UNIQUE → skippar dubbletter
- `players.name` matchas exakt (efter normalisering)
- `has_detail`-flagga → möjliggör retry av missade detaljhämtningar vid omkörning

## Filer

| Fil | Beskrivning |
|-----|-------------|
| `cup_database.py` | `CupDatabase`-klass: schema-initiering, get_or_create-metoder, insert-metoder, namnormalisering |
| `import_cup.py` | `CupImporter`-klass + CLI: `python import_cup.py <tdid>` |
| `cups.db` | SQLite-databas (skapas automatiskt vid första körning) |
| `cups_context.md` | Denna fil |
| `import_logs/cup_{tdid}_{timestamp}.json` | Importlogg med antal deltagare, matcher, legs, throws, errors |
