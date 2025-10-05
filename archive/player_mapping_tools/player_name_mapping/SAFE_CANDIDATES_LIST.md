# Safe Case Variation Candidates - Ready for Mapping

**Generated:** 2025-09-23
**Total Candidates:** 73 MEDIUM-risk candidates identified
**Status:** Ready for manual review and mapping

## Super-Safe Candidates (NO caution factors)

These candidates have same club, no temporal conflicts, and balanced activity:

| # | Player Names | Club | Matches | Risk Level | Notes |
|---|--------------|------|---------|------------|-------|
| 3 | **Johan Brink** / Johan brink | Oilers | 69 vs 10 | MEDIUM | ✅ Perfect candidate |
| 7 | **Roger Strömvall** / Roger strömvall | Mjölner | 35 vs 39 | MEDIUM | ✅ Perfect candidate |
| 8 | **Kenneth Mossfeldt** / Kenneth mossfeldt | Bergsfolket | 41 vs 31 | MEDIUM | ✅ Perfect candidate |
| 9 | **Joakim Silverplats** / Joakim silverplats | IFK Snäsätra | 39 vs 31 | MEDIUM | ✅ Perfect candidate |

## Nearly-Safe Candidates (Minor caution factors)

These have same club but minor temporal overlaps or activity differences:

| # | Player Names | Club | Matches | Caution Factor |
|---|--------------|------|---------|----------------|
| 1 | **Yannick Le Pauvre** / Yannick le Pauvre | Dartanjang | 60 vs 34 | 1 low/medium temporal conflict |
| 2 | **Björn Lejon** / Björn lejon | Bälsta | 73 vs 9 | 1 low/medium temporal conflict |
| 4 | **Guillermo Pomar Lopez** / Guillermo pomar lopez | Bälsta | 70 vs 6 | 1 low/medium temporal conflict |
| 6 | **Paulina Norman** / Paulina norman | Steel Tons | 38 vs 36 | 1 low/medium temporal conflict |
| 10 | **Peter Johansson** / Peter johansson | Bergsfolket | 38 vs 32 | 1 low/medium temporal conflict |
| 12 | **Jocke Olsson** / Jocke olsson | Dartanjang | 42 vs 24 | 2 low/medium temporal conflicts |
| 13 | **Maria Rydell** / Maria rydell | Steel Tons | 43 vs 23 | 1 low/medium temporal conflict |
| 16 | **Joop Van Gerwen** / Joop van Gerwen | Mjölner | 28 vs 34 | None |
| 17 | **Petra Alpvik** / Petra alpvik | Sweden Capital | 34 vs 28 | None |
| 19 | **Gareth Young** / Gareth young | Dartanjang | 24 vs 36 | None |
| 20 | **Magnus Brolin** / Magnus brolin | AC DC | 25 vs 35 | None |

## Complete Top 20 List

Full output from analysis with all details:

```
 1. Yannick Le Pauvre vs Yannick le Pauvre (Dartanjang, 60 vs 34, total: 94)
 2. Björn Lejon vs Björn lejon (Bälsta, 73 vs 9, total: 82)
 3. Johan Brink vs Johan brink (Oilers, 69 vs 10, total: 79) ⭐
 4. Guillermo Pomar Lopez vs Guillermo pomar lopez (Bälsta, 70 vs 6, total: 76)
 5. Anki Nilsson vs Anki nilsson (Steel Tons, 11 vs 63, total: 74)
 6. Paulina Norman vs Paulina norman (Steel Tons, 38 vs 36, total: 74)
 7. Roger Strömvall vs Roger strömvall (Mjölner, 35 vs 39, total: 74) ⭐
 8. Kenneth Mossfeldt vs Kenneth mossfeldt (Bergsfolket, 41 vs 31, total: 72) ⭐
 9. Joakim Silverplats vs Joakim silverplats (IFK Snäsätra, 39 vs 31, total: 70) ⭐
10. Peter Johansson vs Peter johansson (Bergsfolket, 38 vs 32, total: 70)
11. Andreas Hugosson vs Andreas hugosson (Rockhangers, 60 vs 6, total: 66)
12. Jocke Olsson vs Jocke olsson (Dartanjang, 42 vs 24, total: 66)
13. Maria Rydell vs Maria rydell (Steel Tons, 43 vs 23, total: 66)
14. Niklas Wall vs Niklas wall (Dartanjang, 57 vs 8, total: 65)
15. Stefan Lewenhagen vs Stefan lewenhagen (IFK Snäsätra, 52 vs 11, total: 63)
16. Joop Van Gerwen vs Joop van Gerwen (Mjölner, 28 vs 34, total: 62) ⭐
17. Petra Alpvik vs Petra alpvik (Sweden Capital, 34 vs 28, total: 62) ⭐
18. Åsa Vall vs Åsa vall (Åsmo, 43 vs 19, total: 62)
19. Gareth Young vs Gareth young (Dartanjang, 24 vs 36, total: 60) ⭐
20. Magnus Brolin vs Magnus brolin (AC DC, 25 vs 35, total: 60) ⭐
```

⭐ = No caution factors (safest candidates)

## Recommended Mapping Sequence

### Batch 1 (Start here - 4 candidates):
- Johan Brink → Johan brink
- Roger Strömvall → Roger strömvall
- Kenneth Mossfeldt → Kenneth mossfeldt
- Joakim Silverplats → Joakim silverplats

### Batch 2 (If Batch 1 successful - 4 candidates):
- Joop Van Gerwen → Joop van Gerwen
- Petra Alpvik → Petra alpvik
- Gareth Young → Gareth young
- Magnus Brolin → Magnus brolin

### Batch 3 (With minor cautions - 5 candidates):
- Yannick Le Pauvre → Yannick le Pauvre
- Paulina Norman → Paulina norman
- Peter Johansson → Peter johansson
- Maria Rydell → Maria rydell
- Björn Lejon → Björn lejon

## Commands to Execute

### Check current candidates:
```bash
cd player_name_mapping
python show_easy_candidates.py
```

### For manual mapping (example):
```python
# Template for mapping script
source_player_id = [lowercase_version_id]
target_player_id = [propercase_version_id]
canonical_name = "[Proper Case Name]"
```

### Batch processing:
```bash
python batch_case_mapper.py  # Interactive approval required
```

---

**Next Session Goal:** Map first 8-12 safest candidates
**Total Potential Mappings:** 73 candidates ready for review