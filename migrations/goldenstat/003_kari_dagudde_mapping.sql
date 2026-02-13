-- Mappning: Kari-varianter -> Kari Dagudde (2677)
-- Skapa spelare om den inte finns
INSERT OR IGNORE INTO players (id, name) VALUES (2677, 'Kari Dagudde');

-- Uppdatera befintliga mappningar Kari(805)->Kari(Tyresö DC)(2182)
-- till att peka på Kari Dagudde(2677).
UPDATE sub_match_player_mappings
SET correct_player_id = 2677,
    correct_player_name = 'Kari Dagudde',
    confidence = 100,
    mapping_reason = 'Manual: Kari (Tyresö DC) är Kari Dagudde'
WHERE original_player_id = 805
  AND correct_player_id = 2182;

-- Skapa mappningar för Kari (Tyresö DC):s egna sub-matcher
INSERT OR IGNORE INTO sub_match_player_mappings
    (sub_match_id, original_player_id, correct_player_id, correct_player_name, confidence, mapping_reason)
SELECT smp.sub_match_id, 2182, 2677, 'Kari Dagudde', 100,
       'Manual: Kari (Tyresö DC) är Kari Dagudde'
FROM sub_match_participants smp
WHERE smp.player_id = 2182
  AND NOT EXISTS (
      SELECT 1 FROM sub_match_player_mappings m
      WHERE m.sub_match_id = smp.sub_match_id AND m.original_player_id = 2182
  );

-- Skapa mappningar för Kari Dagudde (SpikKastarna):s egna sub-matcher
INSERT OR IGNORE INTO sub_match_player_mappings
    (sub_match_id, original_player_id, correct_player_id, correct_player_name, confidence, mapping_reason)
SELECT smp.sub_match_id, 2344, 2677, 'Kari Dagudde', 100,
       'Manual: Kari Dagudde (SpikKastarna) är Kari Dagudde'
FROM sub_match_participants smp
WHERE smp.player_id = 2344
  AND NOT EXISTS (
      SELECT 1 FROM sub_match_player_mappings m
      WHERE m.sub_match_id = smp.sub_match_id AND m.original_player_id = 2344
  );
