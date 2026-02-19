-- Marcus Ellfors -> Marcus Elffors (stavfel)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 872, 270, 'Marcus Elffors', 'Marcus Ellfors är Marcus Elffors (stavfel)'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 872)
  AND EXISTS (SELECT 1 FROM players WHERE id = 270);

-- Flytta befintliga deltaganden
UPDATE sub_match_participants SET player_id = 270 WHERE player_id = 872;
