-- Joakim B -> Joakim Blomqvist (via sub_match_player_mappings, inte player_aliases)
-- Använder lagkontext-baserad mappning så att "Joakim B" på andra lag inte påverkas

-- Flytta befintliga deltaganden
UPDATE sub_match_participants SET player_id = 1635 WHERE player_id = 940;

-- Skapa mappningar för historiken (så att auto-resolve med lagkontext fungerar)
INSERT OR IGNORE INTO sub_match_player_mappings
(sub_match_id, original_player_id, correct_player_id, correct_player_name, confidence, mapping_reason)
VALUES
(7035, 940, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Joakim B är Joakim Blomqvist (Oilers)'),
(7037, 940, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Joakim B är Joakim Blomqvist (Oilers)'),
(7067, 940, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Joakim B är Joakim Blomqvist (Oilers)'),
(7068, 940, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Joakim B är Joakim Blomqvist (Oilers)'),
(7131, 940, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Joakim B är Joakim Blomqvist (Oilers)'),
(7132, 940, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Joakim B är Joakim Blomqvist (Oilers)'),
(7230, 940, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Joakim B är Joakim Blomqvist (Oilers)'),
(7232, 940, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Joakim B är Joakim Blomqvist (Oilers)');
