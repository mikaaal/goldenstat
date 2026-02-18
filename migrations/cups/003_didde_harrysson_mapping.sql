-- Map "Didde Harrysson" (id 3351) to "Andreas Harrysson" (id 3609)
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 3351, 3609, 'Didde Harrysson', 'Andreas Harrysson', 'manual_merge'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 3351)
  AND EXISTS (SELECT 1 FROM players WHERE id = 3609);
