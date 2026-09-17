-- Dubbelmatcher som sparats som Singles pa grund av svenska namn.
--
-- Divisioner som SL6 och 1FA skriver "Dubbel 1 (Borta)" i stallet for
-- "Doubles1". Importen kande bara igen engelska "Doubles"/"AD" och satte
-- match_type = 'Singles' pa riktiga dubblar. Pa lagsidan och klubbsidan
-- raknades de darfor som singlar (t.ex. "SINGLAR: 2, DUBBLAR: 0").
--
-- Bara rader dar namnet sager dubbel OCH nagot lag har mer an en spelare
-- rattas, sa att en verklig singel aldrig kan tras om till dubbel.

UPDATE sub_matches
SET match_type = 'Doubles'
WHERE match_type = 'Singles'
  AND (match_name LIKE '%Dubbel%' OR match_name LIKE '%Doubles%')
  AND (
      SELECT MAX(antal) FROM (
          SELECT COUNT(*) AS antal
          FROM sub_match_participants smp
          WHERE smp.sub_match_id = sub_matches.id
          GROUP BY smp.team_number
      )
  ) > 1;
