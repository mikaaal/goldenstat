-- Players registered under the same full name with only accents, case, hyphens or stray
-- punctuation differing, e.g. "Micke Frisen" and "Micke Frisèn" for "Micke Frisén".
-- The variant in the most cups is kept. Single names and initials ("Robin A" / "Robin Å")
-- are left alone, since they need not be the same person.

-- Alfred Wahrén -> Alfred Wahren
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4448, 4116, 'Alfred Wahrén', 'Alfred Wahren', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4448 AND name = 'Alfred Wahrén')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4116 AND name = 'Alfred Wahren');
-- Anna--Lena Vilén -> Anna-Lena Vilén
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 3867, 209, 'Anna--Lena Vilén', 'Anna-Lena Vilén', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 3867 AND name = 'Anna--Lena Vilén')
  AND EXISTS (SELECT 1 FROM players WHERE id = 209 AND name = 'Anna-Lena Vilén');
-- Anna Lena Vilen -> Anna-Lena Vilén
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4661, 209, 'Anna Lena Vilen', 'Anna-Lena Vilén', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4661 AND name = 'Anna Lena Vilen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 209 AND name = 'Anna-Lena Vilén');
-- Björn Flodén -> Björn Floden
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4228, 3638, 'Björn Flodén', 'Björn Floden', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4228 AND name = 'Björn Flodén')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3638 AND name = 'Björn Floden');
-- caie Hjälm -> Caie Hjälm
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 2787, 4563, 'caie Hjälm', 'Caie Hjälm', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2787 AND name = 'caie Hjälm')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4563 AND name = 'Caie Hjälm');
-- Christer Olsen -> Christer Olsén
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4259, 2592, 'Christer Olsen', 'Christer Olsén', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4259 AND name = 'Christer Olsen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2592 AND name = 'Christer Olsén');
-- Elvis Smajić -> Elvis Smajic
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4313, 192, 'Elvis Smajić', 'Elvis Smajic', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4313 AND name = 'Elvis Smajić')
  AND EXISTS (SELECT 1 FROM players WHERE id = 192 AND name = 'Elvis Smajic');
-- Emanuel Pettersson Lyredal -> Emanuel Pettersson-Lyredal
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4974, 1740, 'Emanuel Pettersson Lyredal', 'Emanuel Pettersson-Lyredal', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4974 AND name = 'Emanuel Pettersson Lyredal')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1740 AND name = 'Emanuel Pettersson-Lyredal');
-- Fredrik Görgensèn -> Fredrik Görgensen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4918, 481, 'Fredrik Görgensèn', 'Fredrik Görgensen', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4918 AND name = 'Fredrik Görgensèn')
  AND EXISTS (SELECT 1 FROM players WHERE id = 481 AND name = 'Fredrik Görgensen');
-- hannes Björk -> Hannes Björk
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 3172, 4884, 'hannes Björk', 'Hannes Björk', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 3172 AND name = 'hannes Björk')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4884 AND name = 'Hannes Björk');
-- Ica-Stig -> Ica Stig
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6453, 467, 'Ica-Stig', 'Ica Stig', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6453 AND name = 'Ica-Stig')
  AND EXISTS (SELECT 1 FROM players WHERE id = 467 AND name = 'Ica Stig');
-- Isak Sewón -> Isak Sewon
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4875, 175, 'Isak Sewón', 'Isak Sewon', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4875 AND name = 'Isak Sewón')
  AND EXISTS (SELECT 1 FROM players WHERE id = 175 AND name = 'Isak Sewon');
-- Jimmy Petren -> Jimmy Petrén
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4886, 1310, 'Jimmy Petren', 'Jimmy Petrén', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4886 AND name = 'Jimmy Petren')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1310 AND name = 'Jimmy Petrén');
-- Joel Rod? -> Joel Rod
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4202, 273, 'Joel Rod?', 'Joel Rod', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4202 AND name = 'Joel Rod?')
  AND EXISTS (SELECT 1 FROM players WHERE id = 273 AND name = 'Joel Rod');
-- Johan Blomberg.thålin -> Johan Blomberg Thålin
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4888, 1235, 'Johan Blomberg.thålin', 'Johan Blomberg Thålin', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4888 AND name = 'Johan Blomberg.thålin')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1235 AND name = 'Johan Blomberg Thålin');
-- Kalle Goden -> Kalle Godén
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4768, 4501, 'Kalle Goden', 'Kalle Godén', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4768 AND name = 'Kalle Goden')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4501 AND name = 'Kalle Godén');
-- Lars Göran Ohlsson -> Lars-Göran Ohlsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6175, 6237, 'Lars Göran Ohlsson', 'Lars-Göran Ohlsson', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6175 AND name = 'Lars Göran Ohlsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6237 AND name = 'Lars-Göran Ohlsson');
-- ludvig Andersson -> Ludvig Andersson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 2903, 4277, 'ludvig Andersson', 'Ludvig Andersson', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2903 AND name = 'ludvig Andersson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4277 AND name = 'Ludvig Andersson');
-- Måns Åhlberg -> Måns Ahlberg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 624, 648, 'Måns Åhlberg', 'Måns Ahlberg', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 624 AND name = 'Måns Åhlberg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 648 AND name = 'Måns Ahlberg');
-- Martin Ross Langley -> Martin Ross-Langley
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 3618, 2779, 'Martin Ross Langley', 'Martin Ross-Langley', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 3618 AND name = 'Martin Ross Langley')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2779 AND name = 'Martin Ross-Langley');
-- Mattias Kaliszczak . -> Mattias Kaliszczak
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4270, 339, 'Mattias Kaliszczak .', 'Mattias Kaliszczak', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4270 AND name = 'Mattias Kaliszczak .')
  AND EXISTS (SELECT 1 FROM players WHERE id = 339 AND name = 'Mattias Kaliszczak');
-- Miche García -> Miche Garcia
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4017, 296, 'Miche García', 'Miche Garcia', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4017 AND name = 'Miche García')
  AND EXISTS (SELECT 1 FROM players WHERE id = 296 AND name = 'Miche Garcia');
-- Micke Frisen -> Micke Frisén
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4495, 705, 'Micke Frisen', 'Micke Frisén', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4495 AND name = 'Micke Frisen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 705 AND name = 'Micke Frisén');
-- Micke Frisèn -> Micke Frisén
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5347, 705, 'Micke Frisèn', 'Micke Frisén', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5347 AND name = 'Micke Frisèn')
  AND EXISTS (SELECT 1 FROM players WHERE id = 705 AND name = 'Micke Frisén');
-- Mika Alén -> Mika Alen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 2616, 3905, 'Mika Alén', 'Mika Alen', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2616 AND name = 'Mika Alén')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3905 AND name = 'Mika Alen');
-- Moa Strandlund-Palmberg -> Moa Strandlund Palmberg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 1155, 4889, 'Moa Strandlund-Palmberg', 'Moa Strandlund Palmberg', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1155 AND name = 'Moa Strandlund-Palmberg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4889 AND name = 'Moa Strandlund Palmberg');
-- Rickard Sieverts... -> Rickard Sieverts
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4273, 217, 'Rickard Sieverts...', 'Rickard Sieverts', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4273 AND name = 'Rickard Sieverts...')
  AND EXISTS (SELECT 1 FROM players WHERE id = 217 AND name = 'Rickard Sieverts');
-- Sandra Kanté -> Sandra Kante
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 3932, 3250, 'Sandra Kanté', 'Sandra Kante', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 3932 AND name = 'Sandra Kanté')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3250 AND name = 'Sandra Kante');
-- simon Jansson -> Simon Jansson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 3072, 4899, 'simon Jansson', 'Simon Jansson', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 3072 AND name = 'simon Jansson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4899 AND name = 'Simon Jansson');
-- Tina Torénius -> Tina Torenius
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5077, 5479, 'Tina Torénius', 'Tina Torenius', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5077 AND name = 'Tina Torénius')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5479 AND name = 'Tina Torenius');
-- Tony Torénius -> Tony Torenius
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5796, 4900, 'Tony Torénius', 'Tony Torenius', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5796 AND name = 'Tony Torénius')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4900 AND name = 'Tony Torenius');
-- Torbjörn Åhlén -> Torbjörn Åhlen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 3736, 4019, 'Torbjörn Åhlén', 'Torbjörn Åhlen', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 3736 AND name = 'Torbjörn Åhlén')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4019 AND name = 'Torbjörn Åhlen');
-- Waldek Czyż -> Waldek Czyz
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5044, 700, 'Waldek Czyż', 'Waldek Czyz', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5044 AND name = 'Waldek Czyż')
  AND EXISTS (SELECT 1 FROM players WHERE id = 700 AND name = 'Waldek Czyz');
