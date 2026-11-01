-- Goldtown DR 1 Herrar Singel (t_TaHO_8788) had the seeding in front of each name,
-- "16Jonas Norling", which made 39 new players. Every one of them already exists without the
-- number, from the doubles of the same weekend and other cups, so they are merged into those.
-- cup_database.py now drops such a number when importing.

-- 2albin Lindmark -> Albin Lindmark
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7441, 5832, '2albin Lindmark', 'Albin Lindmark', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7441 AND name = '2albin Lindmark')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5832 AND name = 'Albin Lindmark');
-- 3alexander Nordstrand -> Alexander Nordstrand
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7442, 7488, '3alexander Nordstrand', 'Alexander Nordstrand', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7442 AND name = '3alexander Nordstrand')
  AND EXISTS (SELECT 1 FROM players WHERE id = 7488 AND name = 'Alexander Nordstrand');
-- 4alexzander Melander -> Alexzander Melander
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7443, 7490, '4alexzander Melander', 'Alexzander Melander', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7443 AND name = '4alexzander Melander')
  AND EXISTS (SELECT 1 FROM players WHERE id = 7490 AND name = 'Alexzander Melander');
-- 5anders Palo -> Anders Palo
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7444, 6677, '5anders Palo', 'Anders Palo', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7444 AND name = '5anders Palo')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6677 AND name = 'Anders Palo');
-- 6anders Åström -> Anders Åström
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7445, 2204, '6anders Åström', 'Anders Åström', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7445 AND name = '6anders Åström')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2204 AND name = 'Anders Åström');
-- 7carl Fältsjö -> Carl Fältsjö
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7446, 5464, '7carl Fältsjö', 'Carl Fältsjö', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7446 AND name = '7carl Fältsjö')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5464 AND name = 'Carl Fältsjö');
-- 8christoffer Olsson -> Christoffer Olsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7447, 6022, '8christoffer Olsson', 'Christoffer Olsson', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7447 AND name = '8christoffer Olsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6022 AND name = 'Christoffer Olsson');
-- 9daniel Pettersson -> Daniel Pettersson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7448, 3948, '9daniel Pettersson', 'Daniel Pettersson', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7448 AND name = '9daniel Pettersson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3948 AND name = 'Daniel Pettersson');
-- 10dennis Broberg -> Dennis Broberg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7449, 6915, '10dennis Broberg', 'Dennis Broberg', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7449 AND name = '10dennis Broberg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6915 AND name = 'Dennis Broberg');
-- 11eliaz Eriksson Asplund -> Eliaz Eriksson Asplund
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7450, 7492, '11eliaz Eriksson Asplund', 'Eliaz Eriksson Asplund', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7450 AND name = '11eliaz Eriksson Asplund')
  AND EXISTS (SELECT 1 FROM players WHERE id = 7492 AND name = 'Eliaz Eriksson Asplund');
-- 12fredrik Jonsson -> Fredrik Jonsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7451, 6826, '12fredrik Jonsson', 'Fredrik Jonsson', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7451 AND name = '12fredrik Jonsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6826 AND name = 'Fredrik Jonsson');
-- 13isak Hallin -> Isak Hallin
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7452, 7494, '13isak Hallin', 'Isak Hallin', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7452 AND name = '13isak Hallin')
  AND EXISTS (SELECT 1 FROM players WHERE id = 7494 AND name = 'Isak Hallin');
-- 14joel Medelid -> Joel Medelid
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7453, 2515, '14joel Medelid', 'Joel Medelid', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7453 AND name = '14joel Medelid')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2515 AND name = 'Joel Medelid');
-- 15johan Lövgren -> Johan Lövgren
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7454, 5477, '15johan Lövgren', 'Johan Lövgren', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7454 AND name = '15johan Lövgren')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5477 AND name = 'Johan Lövgren');
-- 16jonas Norling -> Jonas Norling
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7455, 170, '16jonas Norling', 'Jonas Norling', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7455 AND name = '16jonas Norling')
  AND EXISTS (SELECT 1 FROM players WHERE id = 170 AND name = 'Jonas Norling');
-- 17jonas Olovsson -> Jonas Olovsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7456, 3777, '17jonas Olovsson', 'Jonas Olovsson', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7456 AND name = '17jonas Olovsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3777 AND name = 'Jonas Olovsson');
-- 18jörgen Karlsson -> Jörgen Karlsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7457, 5614, '18jörgen Karlsson', 'Jörgen Karlsson', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7457 AND name = '18jörgen Karlsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5614 AND name = 'Jörgen Karlsson');
-- 19kenny Johansson -> Kenny Johansson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7458, 6422, '19kenny Johansson', 'Kenny Johansson', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7458 AND name = '19kenny Johansson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6422 AND name = 'Kenny Johansson');
-- 20kevin Fors -> Kevin Fors
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7459, 5639, '20kevin Fors', 'Kevin Fors', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7459 AND name = '20kevin Fors')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5639 AND name = 'Kevin Fors');
-- 21lars Heimdal -> Lars Heimdal
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7460, 7489, '21lars Heimdal', 'Lars Heimdal', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7460 AND name = '21lars Heimdal')
  AND EXISTS (SELECT 1 FROM players WHERE id = 7489 AND name = 'Lars Heimdal');
-- 22liam Nordström -> Liam Nordström
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7461, 2252, '22liam Nordström', 'Liam Nordström', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7461 AND name = '22liam Nordström')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2252 AND name = 'Liam Nordström');
-- 23mats Coreth -> Mats Coreth
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7462, 5693, '23mats Coreth', 'Mats Coreth', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7462 AND name = '23mats Coreth')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5693 AND name = 'Mats Coreth');
-- 24mattias Enmark -> Mattias Enmark
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7463, 3061, '24mattias Enmark', 'Mattias Enmark', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7463 AND name = '24mattias Enmark')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3061 AND name = 'Mattias Enmark');
-- 25morgan Karlsson -> Morgan Karlsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7464, 5478, '25morgan Karlsson', 'Morgan Karlsson', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7464 AND name = '25morgan Karlsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5478 AND name = 'Morgan Karlsson');
-- 26mårten Strömberg -> Mårten Strömberg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7465, 4567, '26mårten Strömberg', 'Mårten Strömberg', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7465 AND name = '26mårten Strömberg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4567 AND name = 'Mårten Strömberg');
-- 27patrick Leandersson -> Patrick Leandersson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7466, 4380, '27patrick Leandersson', 'Patrick Leandersson', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7466 AND name = '27patrick Leandersson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4380 AND name = 'Patrick Leandersson');
-- 28patrik Enbuske -> Patrik Enbuske
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7467, 6675, '28patrik Enbuske', 'Patrik Enbuske', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7467 AND name = '28patrik Enbuske')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6675 AND name = 'Patrik Enbuske');
-- 29peder Bergkvist -> Peder Bergkvist
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7468, 7497, '29peder Bergkvist', 'Peder Bergkvist', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7468 AND name = '29peder Bergkvist')
  AND EXISTS (SELECT 1 FROM players WHERE id = 7497 AND name = 'Peder Bergkvist');
-- 30per-Åke Edström -> Per-Åke Edström
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7469, 7493, '30per-Åke Edström', 'Per-Åke Edström', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7469 AND name = '30per-Åke Edström')
  AND EXISTS (SELECT 1 FROM players WHERE id = 7493 AND name = 'Per-Åke Edström');
-- 31peter Barsk -> Peter Barsk
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7470, 7485, '31peter Barsk', 'Peter Barsk', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7470 AND name = '31peter Barsk')
  AND EXISTS (SELECT 1 FROM players WHERE id = 7485 AND name = 'Peter Barsk');
-- 32philip Räihä -> Philip Räihä
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7471, 7495, '32philip Räihä', 'Philip Räihä', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7471 AND name = '32philip Räihä')
  AND EXISTS (SELECT 1 FROM players WHERE id = 7495 AND name = 'Philip Räihä');
-- 33robert Holmgren -> Robert Holmgren
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7472, 5290, '33robert Holmgren', 'Robert Holmgren', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7472 AND name = '33robert Holmgren')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5290 AND name = 'Robert Holmgren');
-- 34robin Karlsson -> Robin Karlsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7473, 5668, '34robin Karlsson', 'Robin Karlsson', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7473 AND name = '34robin Karlsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5668 AND name = 'Robin Karlsson');
-- 35sam Bodin -> Sam Bodin
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7474, 7491, '35sam Bodin', 'Sam Bodin', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7474 AND name = '35sam Bodin')
  AND EXISTS (SELECT 1 FROM players WHERE id = 7491 AND name = 'Sam Bodin');
-- 36simon Jansson -> Simon Jansson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7475, 4899, '36simon Jansson', 'Simon Jansson', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7475 AND name = '36simon Jansson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4899 AND name = 'Simon Jansson');
-- 37stefan Sehlberg -> Stefan Sehlberg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7476, 7496, '37stefan Sehlberg', 'Stefan Sehlberg', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7476 AND name = '37stefan Sehlberg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 7496 AND name = 'Stefan Sehlberg');
-- 38thomas Ivarsson -> Thomas Ivarsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7477, 7480, '38thomas Ivarsson', 'Thomas Ivarsson', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7477 AND name = '38thomas Ivarsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 7480 AND name = 'Thomas Ivarsson');
-- 39tomas Vedestig -> Tomas Vedestig
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7478, 6682, '39tomas Vedestig', 'Tomas Vedestig', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7478 AND name = '39tomas Vedestig')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6682 AND name = 'Tomas Vedestig');
-- 40tony Torénius -> Tony Torénius
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7479, 5796, '40tony Torénius', 'Tony Torénius', 'seed_number'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7479 AND name = '40tony Torénius')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5796 AND name = 'Tony Torénius');

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
