-- Robert Goht -> Robert Goth (stavfel)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 256, 2322, 'Robert Goth', 'Robert Goht är Robert Goth (stavfel)'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 256)
  AND EXISTS (SELECT 1 FROM players WHERE id = 2322);

-- Flytta befintliga deltaganden
UPDATE sub_match_participants SET player_id = 2322 WHERE player_id = 256;
