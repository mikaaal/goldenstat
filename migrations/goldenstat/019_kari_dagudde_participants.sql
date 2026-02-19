-- Kari (Tyresö DC) -> Kari Dagudde (alias finns redan, flytta deltaganden)
UPDATE sub_match_participants SET player_id = 2677 WHERE player_id = 2182;

-- Kari -> Kari Dagudde (förnamn, sub_match_player_mappings med lagkontext)
INSERT OR IGNORE INTO sub_match_player_mappings
(sub_match_id, original_player_id, correct_player_id, correct_player_name, confidence, mapping_reason)
SELECT smp.sub_match_id, 805, 2677, 'Kari Dagudde', 95, 'Manuell mappning - Kari (Tyresö) är Kari Dagudde'
FROM sub_match_participants smp
WHERE smp.player_id = 805;

UPDATE sub_match_participants SET player_id = 2677 WHERE player_id = 805;
