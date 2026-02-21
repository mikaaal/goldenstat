-- Fix alla player_aliases som pekar på fel spelare pga hardkodade IDs.
-- Denna migration slår upp rätt ID via spelarnamn istället.

-- Steg 1: Fixa player_aliases där canonical_player_id pekar på fel spelare
-- Uppdatera canonical_player_id baserat på canonical_player_name
UPDATE player_aliases
SET canonical_player_id = (
    SELECT p.id FROM players p WHERE p.name = player_aliases.canonical_player_name LIMIT 1
)
WHERE canonical_player_id NOT IN (
    SELECT id FROM players WHERE name = player_aliases.canonical_player_name
)
AND EXISTS (
    SELECT 1 FROM players WHERE name = player_aliases.canonical_player_name
);

-- Steg 2: Fixa player_aliases där alias_player_id pekar på fel spelare
-- Ta bort aliases där alias-spelaren inte finns
DELETE FROM player_aliases
WHERE alias_player_id NOT IN (SELECT id FROM players);

-- Ta bort aliases där canonical-spelaren inte finns
DELETE FROM player_aliases
WHERE canonical_player_id NOT IN (SELECT id FROM players);

-- Steg 3: Fixa sub_match_player_mappings där correct_player_id inte matchar correct_player_name
UPDATE sub_match_player_mappings
SET correct_player_id = (
    SELECT p.id FROM players p WHERE p.name = sub_match_player_mappings.correct_player_name LIMIT 1
)
WHERE correct_player_id NOT IN (
    SELECT id FROM players WHERE name = sub_match_player_mappings.correct_player_name
)
AND EXISTS (
    SELECT 1 FROM players WHERE name = sub_match_player_mappings.correct_player_name
);

-- Steg 4: Fixa sub_match_participants som pekar på alias-spelare
-- Flytta deltaganden till kanonisk spelare
UPDATE sub_match_participants
SET player_id = (
    SELECT pa.canonical_player_id FROM player_aliases pa
    WHERE pa.alias_player_id = sub_match_participants.player_id
)
WHERE player_id IN (SELECT alias_player_id FROM player_aliases);
