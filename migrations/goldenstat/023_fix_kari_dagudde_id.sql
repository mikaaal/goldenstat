-- Fix: Kari Dagudde hade fel ID (2677 kan vara en annan spelare beroende på db-version)
-- Skapa Kari Dagudde om hen inte finns, flytta deltaganden och fixa aliases

-- Skapa Kari Dagudde om spelaren inte redan finns
INSERT OR IGNORE INTO players (name) VALUES ('Kari Dagudde');

-- Flytta deltaganden från id 2677 till rätt Kari Dagudde OM id 2677 inte är Kari Dagudde
UPDATE sub_match_participants
SET player_id = (SELECT id FROM players WHERE name = 'Kari Dagudde' LIMIT 1)
WHERE player_id = 2677
  AND (SELECT name FROM players WHERE id = 2677) != 'Kari Dagudde';

-- Fixa player_aliases som pekar på 2677
UPDATE player_aliases
SET canonical_player_id = (SELECT id FROM players WHERE name = 'Kari Dagudde' LIMIT 1),
    canonical_player_name = 'Kari Dagudde'
WHERE canonical_player_id = 2677
  AND canonical_player_name = 'Kari Dagudde';

-- Fixa sub_match_player_mappings som pekar på 2677 med Kari Dagudde som namn
UPDATE sub_match_player_mappings
SET correct_player_id = (SELECT id FROM players WHERE name = 'Kari Dagudde' LIMIT 1)
WHERE correct_player_id = 2677
  AND correct_player_name = 'Kari Dagudde';
