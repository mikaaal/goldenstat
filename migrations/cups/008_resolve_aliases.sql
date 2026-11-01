-- An alias of an alias (e.g. "John Vesterlund (AIK Dartförening)" -> "John Vesterlund" ->
-- "John Westerlund") was not counted for the final player, since the site and the import only
-- follow one step. Point every alias straight at the final player. Repeated for longer chains.

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
