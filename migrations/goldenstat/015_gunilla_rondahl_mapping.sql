-- Gunilla Rohndal -> Gunilla Rondahl (stavfel)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1351, 991, 'Gunilla Rondahl', 'Gunilla Rohndal är Gunilla Rondahl (stavfel)'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1351)
  AND EXISTS (SELECT 1 FROM players WHERE id = 991);

-- Flytta befintliga deltaganden
UPDATE sub_match_participants SET player_id = 991 WHERE player_id = 1351;
