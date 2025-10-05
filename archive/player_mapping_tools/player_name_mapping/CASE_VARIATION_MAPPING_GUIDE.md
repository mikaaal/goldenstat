# Case Variation Mapping System - Session Guide

## Overview
Vi har byggt ett säkert system för att mappa case-variationer av spelare (t.ex. "Marcus Gavander" vs "Marcus gavander"). Efter tidigare misstag som "gick åt helvete" har vi utvecklat ett mycket försiktigt system som ALLTID kräver manuell godkännande.

## Status (2025-09-23)

### ✅ Redan Mappat
- **Marcus Gavander ↔ Marcus gavander** - 20 sub-matcher mappade (verifierat säkert)

### 🎯 Nästa Steg - Säkra Kandidater Redo för Mappning

Vi har identifierat **73 MEDIUM-risk kandidater** där alla har samma klubb och låga konflikter.

#### **Super-säkra kandidater (INGA caution factors):**
1. **Johan Brink / Johan brink** (Oilers, 69 vs 10 matcher)
2. **Roger Strömvall / Roger strömvall** (Mjölner, 35 vs 39 matcher)
3. **Kenneth Mossfeldt / Kenneth mossfeldt** (Bergsfolket, 41 vs 31 matcher)
4. **Joakim Silverplats / Joakim silverplats** (IFK Snäsätra, 39 vs 31 matcher)

#### **Nästan säkra kandidater (små caution factors):**
5. **Yannick Le Pauvre / Yannick le Pauvre** (Dartanjang, 60 vs 34 matcher)
6. **Björn Lejon / Björn lejon** (Bälsta, 73 vs 9 matcher)
7. **Guillermo Pomar Lopez / Guillermo pomar lopez** (Bälsta, 70 vs 6 matcher)
8. **Paulina Norman / Paulina norman** (Steel Tons, 38 vs 36 matcher)

## Utvecklade Verktyg

### 🔍 Analysverktyg
- **`safe_case_mapper.py`** - Hittar och analyserar case-variationer (INGEN auto-mappning)
- **`show_easy_candidates.py`** - Visar de 20 säkraste kandidaterna
- **`rigorous_case_validator.py`** - Djup validering med samma kriterier som Peter/Johan-mapparna

### 🛠 Mappningsverktyg
- **`batch_case_mapper.py`** - Hanterar 20 mappningar åt gången med manuell godkännande
- **`apply_marcus_mapping.py`** - Exempel på säker mappningsapplikation
- **`verify_marcus_mapping.py`** - Verifiering av tillämpade mappningar

## Säkerhetskriterier

### ✅ SÄKERT att mappa om:
1. **Samma klubb** - Alla variationer spelar för samma klubb
2. **Inga high-severity konflikter** - Ingen samtidig spel för olika klubbar
3. **Logisk progression** - Tidsmässigt sammanhängande spelperioder

### ❌ INTE säkert att mappa om:
1. **Olika klubbar** - DANGER: Troligen olika personer
2. **High-severity temporal konflikter** - Spelar samtidigt på olika ställen
3. **Mycket olika aktivitetsnivåer** - En har 100+ matcher, andra har <10

## Kommandoguide för Nästa Session

### 1. Se alla säkra kandidater:
```bash
cd player_name_mapping
python show_easy_candidates.py
```

### 2. Analysera specifik kandidat:
```bash
python safe_case_mapper.py  # För full analys av alla
```

### 3. Mappa en specifik kandidat manuellt:
```python
# Skapa script baserat på apply_marcus_mapping.py
source_id = [ID för lowercase version]
target_id = [ID för propercase version]
canonical_name = "[Proper Case Name]"
```

### 4. Batch-mappa flera kandidater:
```bash
python batch_case_mapper.py  # Kräver interaktiv input
```

### 5. Verifiera mappningar:
```bash
python verify_marcus_mapping.py  # Anpassa för andra spelare
```

## Database Schema

### Befintliga Tabeller:
- **`sub_match_player_mappings`** - Där mappningarna lagras
- **`players`** - Ursprungliga spelarnamn
- **`sub_match_participants`** - Deltagande i sub-matcher

### Mappningsstruktur:
```sql
INSERT INTO sub_match_player_mappings (
    sub_match_id,           -- Vilken sub-match
    original_player_id,     -- Ursprunglig spelare (t.ex. "marcus gavander")
    correct_player_id,      -- Korrekt spelare (t.ex. "Marcus Gavander")
    correct_player_name,    -- Kanoniskt namn
    confidence,             -- 95 för case variations
    mapping_reason,         -- "Case variation mapping"
    notes                   -- Ytterligare info
)
```

## Rekommenderad Process för Nästa Session

### Steg 1: Börja med Super-säkra (5-10 min)
```bash
# Mappa de 4 super-säkra kandidaterna först
# Johan Brink, Roger Strömvall, Kenneth Mossfeldt, Joakim Silverplats
```

### Steg 2: Utöka till Nästan-säkra (10-15 min)
```bash
# Om steg 1 går bra, lägg till nästa 4-6 kandidater
# Yannick Le Pauvre, Björn Lejon, etc.
```

### Steg 3: Batch-process (20-30 min)
```bash
# Använd batch_case_mapper.py för att hantera 10-20 åt gången
```

### Steg 4: Verifiering
```bash
# Kontrollera att alla mappningar fungerar korrekt
# Testa några i web-appen
```

## Viktiga Filer att Komma Ihåg

### Huvudfiler:
- **`CASE_VARIATION_MAPPING_GUIDE.md`** - Denna guide
- **`show_easy_candidates.py`** - Börja här för att se kandidater
- **`safe_case_mapper.py`** - Använd för djupanalys

### Backup och Historia:
- **`case_variation_finder.py`** - Första versionen (Unicode-problem)
- **`simple_case_finder.py`** - Förenklad Marcus-analys
- **Marcus-mappnings-filer** - Exempel på genomförda mappningar

## Fel att Undvika

1. **Aldrig auto-mappa** - Alltid manuell granskning först
2. **Dubbelkolla klubbar** - Olika klubbar = olika personer
3. **Validera temporal logik** - Ingen simultan spel på olika ställen
4. **Backup före batch** - Alltid möjlighet att ångra

## Framtida Förbättringar

- **GUI-verktyg** för enklare granskning
- **Performance-analys** för ytterligare validering
- **Automatiserad rapportering** av mappningsresultat
- **Integration med web-appen** för live-testning

---

**Skapad:** 2025-09-23
**Status:** 73 kandidater identifierade, Marcus-mappning genomförd
**Nästa:** Mappa 4-8 super-säkra kandidater