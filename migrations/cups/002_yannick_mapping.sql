-- Map "Yannick" (id 4095) to "Yannick Le Pauvre" (id 280)
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4095, 280, 'Yannick', 'Yannick Le Pauvre', 'manual_merge'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4095)
  AND EXISTS (SELECT 1 FROM players WHERE id = 280);
