-- Peter Book also played the Oilers cups as "Book", "Booken", "Booken P" and "Boken". None of
-- them ever played a cup together with Peter Book or with each other, while he played 8-26 cups
-- a month over the same time, their averages are close to his, and "Book" played doubles with
-- "Janas", one of his usual partners.

-- Book -> Peter Book
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5921, 146, 'Book', 'Peter Book', 'nickname'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5921 AND name = 'Book')
  AND EXISTS (SELECT 1 FROM players WHERE id = 146 AND name = 'Peter Book');
-- Booken -> Peter Book
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6032, 146, 'Booken', 'Peter Book', 'nickname'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6032 AND name = 'Booken')
  AND EXISTS (SELECT 1 FROM players WHERE id = 146 AND name = 'Peter Book');
-- Booken P -> Peter Book
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9146, 146, 'Booken P', 'Peter Book', 'nickname'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9146 AND name = 'Booken P')
  AND EXISTS (SELECT 1 FROM players WHERE id = 146 AND name = 'Peter Book');
-- Boken -> Peter Book
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9181, 146, 'Boken', 'Peter Book', 'nickname'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9181 AND name = 'Boken')
  AND EXISTS (SELECT 1 FROM players WHERE id = 146 AND name = 'Peter Book');

-- As in 008: point aliases of aliases at the final player and move the links over.

UPDATE cup_player_mappings
SET canonical_player_id = (SELECT b.canonical_player_id FROM cup_player_mappings b
                           WHERE b.alias_player_id = cup_player_mappings.canonical_player_id),
    canonical_name = (SELECT b.canonical_name FROM cup_player_mappings b
                      WHERE b.alias_player_id = cup_player_mappings.canonical_player_id)
WHERE canonical_player_id IN (SELECT alias_player_id FROM cup_player_mappings)
  AND canonical_player_id != alias_player_id;

UPDATE cup_player_mappings
SET canonical_player_id = (SELECT b.canonical_player_id FROM cup_player_mappings b
                           WHERE b.alias_player_id = cup_player_mappings.canonical_player_id),
    canonical_name = (SELECT b.canonical_name FROM cup_player_mappings b
                      WHERE b.alias_player_id = cup_player_mappings.canonical_player_id)
WHERE canonical_player_id IN (SELECT alias_player_id FROM cup_player_mappings)
  AND canonical_player_id != alias_player_id;

UPDATE cup_player_mappings
SET canonical_player_id = (SELECT b.canonical_player_id FROM cup_player_mappings b
                           WHERE b.alias_player_id = cup_player_mappings.canonical_player_id),
    canonical_name = (SELECT b.canonical_name FROM cup_player_mappings b
                      WHERE b.alias_player_id = cup_player_mappings.canonical_player_id)
WHERE canonical_player_id IN (SELECT alias_player_id FROM cup_player_mappings)
  AND canonical_player_id != alias_player_id;

UPDATE cup_player_mappings
SET canonical_player_id = (SELECT b.canonical_player_id FROM cup_player_mappings b
                           WHERE b.alias_player_id = cup_player_mappings.canonical_player_id),
    canonical_name = (SELECT b.canonical_name FROM cup_player_mappings b
                      WHERE b.alias_player_id = cup_player_mappings.canonical_player_id)
WHERE canonical_player_id IN (SELECT alias_player_id FROM cup_player_mappings)
  AND canonical_player_id != alias_player_id;

-- canonical_name is shown in match lists, so keep it equal to the player's current name
UPDATE cup_player_mappings
SET canonical_name = (SELECT name FROM players WHERE id = cup_player_mappings.canonical_player_id)
WHERE canonical_name != (SELECT name FROM players WHERE id = cup_player_mappings.canonical_player_id);

-- Only some queries look at cup_player_mappings, so links still on an alias move to the
-- final player, as review_typos.py does. A pair already linked to both keeps one link.
DELETE FROM participant_players
WHERE player_id IN (SELECT alias_player_id FROM cup_player_mappings)
  AND EXISTS (
      SELECT 1 FROM participant_players pp
      JOIN cup_player_mappings m ON m.canonical_player_id = pp.player_id
      WHERE m.alias_player_id = participant_players.player_id
        AND pp.participant_id = participant_players.participant_id
  );

UPDATE participant_players
SET player_id = (SELECT canonical_player_id FROM cup_player_mappings
                 WHERE alias_player_id = participant_players.player_id)
WHERE player_id IN (SELECT alias_player_id FROM cup_player_mappings);
