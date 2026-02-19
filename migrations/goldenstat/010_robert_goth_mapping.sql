-- Robert Goth (Aik) -> Robert Goth
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 579, 2322, 'Robert Goth', 'Robert Goth (Aik) är Robert Goth'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 579)
  AND EXISTS (SELECT 1 FROM players WHERE id = 2322);

-- Robert Goth (Mitt i DC) -> Robert Goth
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2323, 2322, 'Robert Goth', 'Robert Goth (Mitt i DC) är Robert Goth'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2323)
  AND EXISTS (SELECT 1 FROM players WHERE id = 2322);

-- Flytta befintliga deltaganden
UPDATE sub_match_participants SET player_id = 2322 WHERE player_id = 579;
UPDATE sub_match_participants SET player_id = 2322 WHERE player_id = 2323;
