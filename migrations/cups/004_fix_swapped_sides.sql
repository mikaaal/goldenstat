-- Vänd tillbaka sidorna i cupmatcher där legdatan importerats med sida 1/2
-- omkastade. import_cup.py vände sidorna när matchen hämtats med omvänd tmid,
-- men n01 returnerar ändå sidorna i p1/p2-ordning. Kontrollen av snitt efteråt
-- missade matcher där spelarnas snitt låg nära varandra.
--
-- En match räknas som vänd när vunna legs per sida i legs är exakt omvänt mot
-- resultatet (p1_legs_won/p2_legs_won från turneringsdatan). Oavgjorda matcher
-- går inte att avgöra och lämnas orörda. Stickprov mot n01 (turnering 1224,
-- 799 och 372) gav samma matcher som den här kontrollen.
BEGIN;

CREATE TEMP TABLE swapped_cup_matches AS
SELECT m.id
FROM cup_matches m
JOIN (
    SELECT cup_match_id, SUM(winner_side = 1) AS w1, SUM(winner_side = 2) AS w2
    FROM legs
    GROUP BY cup_match_id
) l ON l.cup_match_id = m.id
WHERE m.has_detail = 1
  AND m.p1_legs_won != m.p2_legs_won
  AND m.p1_legs_won = l.w2
  AND m.p2_legs_won = l.w1;

UPDATE throws SET side_number = 3 - side_number
WHERE leg_id IN (
    SELECT id FROM legs WHERE cup_match_id IN (SELECT id FROM swapped_cup_matches)
);

-- winner_side 0 och 3 förekommer i äldre data och lämnas som de är
UPDATE legs
SET winner_side = CASE WHEN winner_side IN (1, 2) THEN 3 - winner_side ELSE winner_side END,
    first_side = 3 - first_side
WHERE cup_match_id IN (SELECT id FROM swapped_cup_matches);

DROP TABLE swapped_cup_matches;

COMMIT;
