-- Easts Poängsamlarcup FINAL, 2025-26 (t_bhMr_3121) was a handicap cup with each
-- player's average after the name, "JOCKE EKNER 21,83", which made 46 new players. They all
-- already exist without the average and are merged into those. cup_database.py now drops a
-- decimal number after a full name when importing.

-- Ingus Grandbergs 18,5 -> Ingus Grandbergs
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9264, 11, 'Ingus Grandbergs 18,5', 'Ingus Grandbergs', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9264 AND name = 'Ingus Grandbergs 18,5')
  AND EXISTS (SELECT 1 FROM players WHERE id = 11 AND name = 'Ingus Grandbergs');
-- Jocke Ekner 21,83 -> Jocke Ekner
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9265, 14, 'Jocke Ekner 21,83', 'Jocke Ekner', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9265 AND name = 'Jocke Ekner 21,83')
  AND EXISTS (SELECT 1 FROM players WHERE id = 14 AND name = 'Jocke Ekner');
-- Peter Book 19,93 -> Peter Book
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9266, 146, 'Peter Book 19,93', 'Peter Book', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9266 AND name = 'Peter Book 19,93')
  AND EXISTS (SELECT 1 FROM players WHERE id = 146 AND name = 'Peter Book');
-- Hans Pedersen 17,37 -> Hans Pedersen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9267, 172, 'Hans Pedersen 17,37', 'Hans Pedersen', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9267 AND name = 'Hans Pedersen 17,37')
  AND EXISTS (SELECT 1 FROM players WHERE id = 172 AND name = 'Hans Pedersen');
-- Axel Edström 18,01 -> Axel Edström
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9268, 4226, 'Axel Edström 18,01', 'Axel Edström', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9268 AND name = 'Axel Edström 18,01')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4226 AND name = 'Axel Edström');
-- Robert Södervall 18,3 -> Robert Södervall
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9269, 190, 'Robert Södervall 18,3', 'Robert Södervall', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9269 AND name = 'Robert Södervall 18,3')
  AND EXISTS (SELECT 1 FROM players WHERE id = 190 AND name = 'Robert Södervall');
-- Alex Mekonnen 20,16 -> Alex Mekonnen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9270, 57, 'Alex Mekonnen 20,16', 'Alex Mekonnen', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9270 AND name = 'Alex Mekonnen 20,16')
  AND EXISTS (SELECT 1 FROM players WHERE id = 57 AND name = 'Alex Mekonnen');
-- Noah Lind 18,11 -> Noah Lind
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9271, 31, 'Noah Lind 18,11', 'Noah Lind', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9271 AND name = 'Noah Lind 18,11')
  AND EXISTS (SELECT 1 FROM players WHERE id = 31 AND name = 'Noah Lind');
-- Sebastian Sellén 18,02 -> Sebastian Sellén
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9272, 177, 'Sebastian Sellén 18,02', 'Sebastian Sellén', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9272 AND name = 'Sebastian Sellén 18,02')
  AND EXISTS (SELECT 1 FROM players WHERE id = 177 AND name = 'Sebastian Sellén');
-- Anders Lind 17,2 -> Anders Lind
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9273, 3, 'Anders Lind 17,2', 'Anders Lind', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9273 AND name = 'Anders Lind 17,2')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3 AND name = 'Anders Lind');
-- Magnus Eriksson 19,49 -> Magnus Eriksson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9274, 28, 'Magnus Eriksson 19,49', 'Magnus Eriksson', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9274 AND name = 'Magnus Eriksson 19,49')
  AND EXISTS (SELECT 1 FROM players WHERE id = 28 AND name = 'Magnus Eriksson');
-- Bee Ekner 13,1 -> Bee Ekner
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9275, 5, 'Bee Ekner 13,1', 'Bee Ekner', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9275 AND name = 'Bee Ekner 13,1')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5 AND name = 'Bee Ekner');
-- Stefan "Sidan" Sundberg 20,09 -> Stefan "Sidan" Sundberg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9276, 174, 'Stefan "Sidan" Sundberg 20,09', 'Stefan "Sidan" Sundberg', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9276 AND name = 'Stefan "Sidan" Sundberg 20,09')
  AND EXISTS (SELECT 1 FROM players WHERE id = 174 AND name = 'Stefan "Sidan" Sundberg');
-- Robert Nilsson 15,02 -> Robert Nilsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9277, 19, 'Robert Nilsson 15,02', 'Robert Nilsson', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9277 AND name = 'Robert Nilsson 15,02')
  AND EXISTS (SELECT 1 FROM players WHERE id = 19 AND name = 'Robert Nilsson');
-- Ronny Johansson 15,10 -> Ronny Johansson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9278, 20, 'Ronny Johansson 15,10', 'Ronny Johansson', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9278 AND name = 'Ronny Johansson 15,10')
  AND EXISTS (SELECT 1 FROM players WHERE id = 20 AND name = 'Ronny Johansson');
-- Ted Åbom 18,24 -> Ted Åbom
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9279, 47, 'Ted Åbom 18,24', 'Ted Åbom', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9279 AND name = 'Ted Åbom 18,24')
  AND EXISTS (SELECT 1 FROM players WHERE id = 47 AND name = 'Ted Åbom');
-- Mika Hautamäki 18,51 -> Mika Hautamäki
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9280, 41, 'Mika Hautamäki 18,51', 'Mika Hautamäki', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9280 AND name = 'Mika Hautamäki 18,51')
  AND EXISTS (SELECT 1 FROM players WHERE id = 41 AND name = 'Mika Hautamäki');
-- Matt Collins 17,5 -> Matt Collins
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9281, 46, 'Matt Collins 17,5', 'Matt Collins', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9281 AND name = 'Matt Collins 17,5')
  AND EXISTS (SELECT 1 FROM players WHERE id = 46 AND name = 'Matt Collins');
-- Anna-Lena Vilén 13,12 -> Anna-Lena Vilén
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9282, 209, 'Anna-Lena Vilén 13,12', 'Anna-Lena Vilén', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9282 AND name = 'Anna-Lena Vilén 13,12')
  AND EXISTS (SELECT 1 FROM players WHERE id = 209 AND name = 'Anna-Lena Vilén');
-- Maud Jansson 18.95 -> Maud Jansson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9283, 88, 'Maud Jansson 18.95', 'Maud Jansson', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9283 AND name = 'Maud Jansson 18.95')
  AND EXISTS (SELECT 1 FROM players WHERE id = 88 AND name = 'Maud Jansson');
-- Ancie Fernström 13,16 -> Ancie Fernström
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9284, 2, 'Ancie Fernström 13,16', 'Ancie Fernström', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9284 AND name = 'Ancie Fernström 13,16')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2 AND name = 'Ancie Fernström');
-- Mats Stenlund 16,36 -> Mats Stenlund
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9285, 61, 'Mats Stenlund 16,36', 'Mats Stenlund', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9285 AND name = 'Mats Stenlund 16,36')
  AND EXISTS (SELECT 1 FROM players WHERE id = 61 AND name = 'Mats Stenlund');
-- Henrik Nilsson 19,83 -> Henrik Nilsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9286, 4322, 'Henrik Nilsson 19,83', 'Henrik Nilsson', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9286 AND name = 'Henrik Nilsson 19,83')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4322 AND name = 'Henrik Nilsson');
-- Linus Dellby 18,92 -> Linus Dellby
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9287, 144, 'Linus Dellby 18,92', 'Linus Dellby', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9287 AND name = 'Linus Dellby 18,92')
  AND EXISTS (SELECT 1 FROM players WHERE id = 144 AND name = 'Linus Dellby');
-- Mats Hero 19,99 -> Mats Hero
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9288, 305, 'Mats Hero 19,99', 'Mats Hero', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9288 AND name = 'Mats Hero 19,99')
  AND EXISTS (SELECT 1 FROM players WHERE id = 305 AND name = 'Mats Hero');
-- Frida Persdotter 13,03 -> Frida Persdotter
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9289, 180, 'Frida Persdotter 13,03', 'Frida Persdotter', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9289 AND name = 'Frida Persdotter 13,03')
  AND EXISTS (SELECT 1 FROM players WHERE id = 180 AND name = 'Frida Persdotter');
-- Bernt Ekberg 17,28 -> Bernt Ekberg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9290, 6, 'Bernt Ekberg 17,28', 'Bernt Ekberg', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9290 AND name = 'Bernt Ekberg 17,28')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6 AND name = 'Bernt Ekberg');
-- Tomas Faleroth 16,10 -> Tomas Faleroth
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9291, 23, 'Tomas Faleroth 16,10', 'Tomas Faleroth', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9291 AND name = 'Tomas Faleroth 16,10')
  AND EXISTS (SELECT 1 FROM players WHERE id = 23 AND name = 'Tomas Faleroth');
-- Anna Felldin 12,61 -> Anna Felldin
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9292, 4, 'Anna Felldin 12,61', 'Anna Felldin', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9292 AND name = 'Anna Felldin 12,61')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4 AND name = 'Anna Felldin');
-- Henrik Hollsten, 14,81 -> Henrik Hollsten
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9293, 76, 'Henrik Hollsten, 14,81', 'Henrik Hollsten', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9293 AND name = 'Henrik Hollsten, 14,81')
  AND EXISTS (SELECT 1 FROM players WHERE id = 76 AND name = 'Henrik Hollsten');
-- Anders Lindqvist 16,14 -> Anders Lindqvist
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9294, 65, 'Anders Lindqvist 16,14', 'Anders Lindqvist', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9294 AND name = 'Anders Lindqvist 16,14')
  AND EXISTS (SELECT 1 FROM players WHERE id = 65 AND name = 'Anders Lindqvist');
-- Peter "Isak" Isaksson 18, 7 -> Peter "Isak" Isaksson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9295, 207, 'Peter "Isak" Isaksson 18, 7', 'Peter "Isak" Isaksson', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9295 AND name = 'Peter "Isak" Isaksson 18, 7')
  AND EXISTS (SELECT 1 FROM players WHERE id = 207 AND name = 'Peter "Isak" Isaksson');
-- Chris Broughall 15,51 -> Chris Broughall
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9296, 171, 'Chris Broughall 15,51', 'Chris Broughall', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9296 AND name = 'Chris Broughall 15,51')
  AND EXISTS (SELECT 1 FROM players WHERE id = 171 AND name = 'Chris Broughall');
-- Yannick Le Pauvre 22,38 -> Yannick Le Pauvre
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9297, 280, 'Yannick Le Pauvre 22,38', 'Yannick Le Pauvre', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9297 AND name = 'Yannick Le Pauvre 22,38')
  AND EXISTS (SELECT 1 FROM players WHERE id = 280 AND name = 'Yannick Le Pauvre');
-- Dick Johansson 16,85 -> Dick Johansson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9298, 236, 'Dick Johansson 16,85', 'Dick Johansson', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9298 AND name = 'Dick Johansson 16,85')
  AND EXISTS (SELECT 1 FROM players WHERE id = 236 AND name = 'Dick Johansson');
-- Joacim Jonasson 21,97 -> Joacim Jonasson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9299, 45, 'Joacim Jonasson 21,97', 'Joacim Jonasson', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9299 AND name = 'Joacim Jonasson 21,97')
  AND EXISTS (SELECT 1 FROM players WHERE id = 45 AND name = 'Joacim Jonasson');
-- Dennis Felldin 16,92 -> Dennis Felldin
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9300, 227, 'Dennis Felldin 16,92', 'Dennis Felldin', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9300 AND name = 'Dennis Felldin 16,92')
  AND EXISTS (SELECT 1 FROM players WHERE id = 227 AND name = 'Dennis Felldin');
-- Tommy Söderström 17,26 -> Tommy Söderström
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9301, 26, 'Tommy Söderström 17,26', 'Tommy Söderström', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9301 AND name = 'Tommy Söderström 17,26')
  AND EXISTS (SELECT 1 FROM players WHERE id = 26 AND name = 'Tommy Söderström');
-- Gustav Brückner 21,55 -> Gustav Brückner
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9302, 173, 'Gustav Brückner 21,55', 'Gustav Brückner', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9302 AND name = 'Gustav Brückner 21,55')
  AND EXISTS (SELECT 1 FROM players WHERE id = 173 AND name = 'Gustav Brückner');
-- Patrik Åbrink 16,59 -> Patrik Åbrink
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9303, 68, 'Patrik Åbrink 16,59', 'Patrik Åbrink', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9303 AND name = 'Patrik Åbrink 16,59')
  AND EXISTS (SELECT 1 FROM players WHERE id = 68 AND name = 'Patrik Åbrink');
-- Gustaf Wallner 17,77 -> Gustaf Wallner
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9304, 178, 'Gustaf Wallner 17,77', 'Gustaf Wallner', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9304 AND name = 'Gustaf Wallner 17,77')
  AND EXISTS (SELECT 1 FROM players WHERE id = 178 AND name = 'Gustaf Wallner');
-- Ann Johansson 12,75 -> Ann Johansson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9305, 38, 'Ann Johansson 12,75', 'Ann Johansson', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9305 AND name = 'Ann Johansson 12,75')
  AND EXISTS (SELECT 1 FROM players WHERE id = 38 AND name = 'Ann Johansson');
-- Per-Erik "Bacon" Bredberg 17,75 -> Per-Erik "Bacon" Bredberg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9306, 69, 'Per-Erik "Bacon" Bredberg 17,75', 'Per-Erik "Bacon" Bredberg', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9306 AND name = 'Per-Erik "Bacon" Bredberg 17,75')
  AND EXISTS (SELECT 1 FROM players WHERE id = 69 AND name = 'Per-Erik "Bacon" Bredberg');
-- Alexander Felldin 13,29 -> Alexander Felldin
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9307, 1, 'Alexander Felldin 13,29', 'Alexander Felldin', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9307 AND name = 'Alexander Felldin 13,29')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1 AND name = 'Alexander Felldin');
-- Tony Edström 19,08 -> Tony Edström
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9308, 2039, 'Tony Edström 19,08', 'Tony Edström', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9308 AND name = 'Tony Edström 19,08')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2039 AND name = 'Tony Edström');
-- Stefan "Bobo" Appelbo 18,95 -> Stefan "Bobo" Appelbo
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 9309, 260, 'Stefan "Bobo" Appelbo 18,95', 'Stefan "Bobo" Appelbo', 'average_in_name'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 9309 AND name = 'Stefan "Bobo" Appelbo 18,95')
  AND EXISTS (SELECT 1 FROM players WHERE id = 260 AND name = 'Stefan "Bobo" Appelbo');

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
