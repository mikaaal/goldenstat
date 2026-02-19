-- Uppdatera sub_match_player_mappings som pekar på alias-spelare
-- så att de pekar på kanoniska spelare istället.
-- Annars dyker alias-namnen fortfarande upp i spelarsöken.
UPDATE sub_match_player_mappings
SET correct_player_id = pa.canonical_player_id,
    correct_player_name = pa.canonical_player_name
FROM player_aliases pa
WHERE sub_match_player_mappings.correct_player_id = pa.alias_player_id;
