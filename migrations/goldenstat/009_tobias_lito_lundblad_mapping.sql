-- Tobias Lundblad -> Tobias Lito Lundblad
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1554, 2610, 'Tobias Lito Lundblad', 'Tobias Lundblad är Tobias Lito Lundblad'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1554)
  AND EXISTS (SELECT 1 FROM players WHERE id = 2610);

-- Lito -> Tobias Lito Lundblad
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1331, 2610, 'Tobias Lito Lundblad', 'Lito är Tobias Lito Lundblad'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1331)
  AND EXISTS (SELECT 1 FROM players WHERE id = 2610);

-- Flytta befintliga deltaganden
UPDATE sub_match_participants SET player_id = 2610 WHERE player_id = 1554;
UPDATE sub_match_participants SET player_id = 2610 WHERE player_id = 1331;
