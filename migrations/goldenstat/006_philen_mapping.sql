-- Philen -> Johnny Pihl (smeknamn)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 922, 881, 'Johnny Pihl', 'Philen är Johnny Pihl (smeknamn)'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 922)
  AND EXISTS (SELECT 1 FROM players WHERE id = 881);

-- Flytta befintliga deltaganden
UPDATE sub_match_participants SET player_id = 881 WHERE player_id = 922;
