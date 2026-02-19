-- Johnny Phil -> Johnny Pihl
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2453, 881, 'Johnny Pihl', 'Johnny Phil är Johnny Pihl (stavfel i N01)'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2453)
  AND EXISTS (SELECT 1 FROM players WHERE id = 881);
