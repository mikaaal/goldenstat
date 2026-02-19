-- Jocke (Oilers) -> Joakim Blomqvist (via sub_match_player_mappings, inte player_aliases)

-- Flytta befintliga deltaganden
UPDATE sub_match_participants SET player_id = 1635 WHERE player_id = 2242;

-- Skapa mappningar för historiken
INSERT OR IGNORE INTO sub_match_player_mappings
(sub_match_id, original_player_id, correct_player_id, correct_player_name, confidence, mapping_reason)
VALUES
(5873, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(5875, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(5910, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(5911, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(5932, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(5933, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(5968, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(5969, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(6053, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(6055, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(6081, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(6083, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(6105, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(6106, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(6154, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(6156, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(6174, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(6176, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(6207, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(6208, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(6245, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist'),
(6246, 2242, 1635, 'Joakim Blomqvist', 95, 'Manuell mappning - Jocke (Oilers) är Joakim Blomqvist');
