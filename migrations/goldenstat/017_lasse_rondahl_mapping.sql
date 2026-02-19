-- Lasse Rondahl -> Lars Rondahl (smeknamn)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2681, 2350, 'Lars Rondahl', 'Lasse Rondahl är Lars Rondahl (smeknamn)'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2681)
  AND EXISTS (SELECT 1 FROM players WHERE id = 2350);

-- Flytta befintliga deltaganden
UPDATE sub_match_participants SET player_id = 2350 WHERE player_id = 2681;
