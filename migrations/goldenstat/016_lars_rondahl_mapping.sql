-- Lars Rohndal -> Lars Rondahl (stavfel)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1352, 2350, 'Lars Rondahl', 'Lars Rohndal är Lars Rondahl (stavfel)'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1352)
  AND EXISTS (SELECT 1 FROM players WHERE id = 2350);

-- Flytta befintliga deltaganden
UPDATE sub_match_participants SET player_id = 2350 WHERE player_id = 1352;
