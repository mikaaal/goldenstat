-- Mappning: Bernte (453) och Bernte (SpikKastarna) (2304) -> Bernth Andersson (2352)
-- Uppdatera befintliga mappningar som pekar Bernte(453)->Bernte(SpikKastarna)(2304)
-- till att istället peka på Bernth Andersson(2352).

UPDATE sub_match_player_mappings
SET correct_player_id = 2352,
    correct_player_name = 'Bernth Andersson',
    confidence = 100,
    mapping_reason = 'Manual: Bernte (SpikKastarna) är Bernth Andersson'
WHERE original_player_id = 453
  AND correct_player_id = 2304;

-- Skapa mappningar för Bernte (SpikKastarna):s egna sub-matcher
-- som saknar mappning till Bernth Andersson.
INSERT OR IGNORE INTO sub_match_player_mappings
    (sub_match_id, original_player_id, correct_player_id, correct_player_name, confidence, mapping_reason)
SELECT smp.sub_match_id, 2304, 2352, 'Bernth Andersson', 100,
       'Manual: Bernte (SpikKastarna) är Bernth Andersson'
FROM sub_match_participants smp
WHERE smp.player_id = 2304
  AND NOT EXISTS (
      SELECT 1 FROM sub_match_player_mappings m
      WHERE m.sub_match_id = smp.sub_match_id AND m.original_player_id = 2304
  );
