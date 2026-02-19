-- William Karlsson (Ac Dc) -> William Karlsson
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 897, 2332, 'William Karlsson', 'William Karlsson (Ac Dc) är William Karlsson'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 897)
  AND EXISTS (SELECT 1 FROM players WHERE id = 2332);

-- William Karlsson dubblett -> William Karlsson
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2609, 2332, 'William Karlsson', 'William Karlsson (dubblett) är William Karlsson'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2609)
  AND EXISTS (SELECT 1 FROM players WHERE id = 2332);

-- Flytta befintliga deltaganden
UPDATE sub_match_participants SET player_id = 2332 WHERE player_id = 897;
UPDATE sub_match_participants SET player_id = 2332 WHERE player_id = 2609;
