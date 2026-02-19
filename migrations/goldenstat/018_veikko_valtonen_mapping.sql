-- Veikko (Tyresö DC) -> Veikko Valtonen (player_aliases)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2281, 1534, 'Veikko Valtonen', 'Veikko (Tyresö DC) är Veikko Valtonen'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2281)
  AND EXISTS (SELECT 1 FROM players WHERE id = 1534);

UPDATE sub_match_participants SET player_id = 1534 WHERE player_id = 2281;

-- Veikko -> Veikko Valtonen (sub_match_player_mappings, förnamn med lagkontext)
INSERT OR IGNORE INTO sub_match_player_mappings
(sub_match_id, original_player_id, correct_player_id, correct_player_name, confidence, mapping_reason)
SELECT smp.sub_match_id, 801, 1534, 'Veikko Valtonen', 95, 'Manuell mappning - Veikko (Tyresö) är Veikko Valtonen'
FROM sub_match_participants smp
WHERE smp.player_id = 801;

UPDATE sub_match_participants SET player_id = 1534 WHERE player_id = 801;
