-- Maud (Mitt I Dc) -> Maud Jansson
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2233, 75, 'Maud Jansson', 'Maud (Mitt I Dc) är Maud Jansson'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2233)
  AND EXISTS (SELECT 1 FROM players WHERE id = 75);

-- Maud -> Maud Jansson
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1837, 75, 'Maud Jansson', 'Maud är Maud Jansson'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1837)
  AND EXISTS (SELECT 1 FROM players WHERE id = 75);

-- Flytta befintliga deltaganden
UPDATE sub_match_participants SET player_id = 75 WHERE player_id = 2233;
UPDATE sub_match_participants SET player_id = 75 WHERE player_id = 1837;
