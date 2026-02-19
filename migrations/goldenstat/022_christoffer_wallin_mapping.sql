-- Christoffer Wallin dubblett -> Christoffer Wallin
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 886, 555, 'Christoffer Wallin', 'Christoffer Wallin (dubblett) är Christoffer Wallin'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 886)
  AND EXISTS (SELECT 1 FROM players WHERE id = 555);

-- Stoffe Wallin -> Christoffer Wallin (smeknamn)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1344, 555, 'Christoffer Wallin', 'Stoffe Wallin är Christoffer Wallin (smeknamn)'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1344)
  AND EXISTS (SELECT 1 FROM players WHERE id = 555);

-- Flytta befintliga deltaganden
UPDATE sub_match_participants SET player_id = 555 WHERE player_id = 886;
UPDATE sub_match_participants SET player_id = 555 WHERE player_id = 1344;
