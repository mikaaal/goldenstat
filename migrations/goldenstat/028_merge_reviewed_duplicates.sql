-- The seven groups left out of 027, where two ids played for different clubs in the same season.
-- Reviewed by hand: most are one player who changed or shared clubs. Where it is two people,
-- the one with fewer matches gets the club in the name, as for "Mats Andersson (AIK Dart)".
--
-- The old sub-match mappings between ids in these groups point at sub-matches the original id
-- no longer plays in, so they are dropped and the club of each match decides instead.

DELETE FROM sub_match_player_mappings
WHERE (original_player_id IN (857, 910, 2329) AND correct_player_id IN (857, 910, 2329))
   OR (original_player_id IN (695, 2349, 2371) AND correct_player_id IN (695, 2349, 2371))
   OR (original_player_id IN (100, 1763, 2333, 2334) AND correct_player_id IN (100, 1763, 2333, 2334))
   OR (original_player_id IN (1448, 1817, 2335) AND correct_player_id IN (1448, 1817, 2335))
   OR (original_player_id IN (990, 2346, 2421) AND correct_player_id IN (990, 2346, 2421))
   OR (original_player_id IN (303, 2324, 2326, 2434) AND correct_player_id IN (303, 2324, 2326, 2434))
   OR (original_player_id IN (732, 2320, 2321) AND correct_player_id IN (732, 2320, 2321));

-- Stefan Berg in VH Sportbar is another player than the one in Cobra DC and DIF Dart
UPDATE sub_match_participants SET player_id = 2324
WHERE player_id IN (303, 2324, 2326, 2434)
  AND (SELECT CASE sub_match_participants.team_number WHEN 1 THEN t1.name ELSE t2.name END
       FROM sub_matches sm JOIN matches m ON m.id = sm.match_id
       JOIN teams t1 ON t1.id = m.team1_id JOIN teams t2 ON t2.id = m.team2_id
       WHERE sm.id = sub_match_participants.sub_match_id) LIKE 'VH Sportbar%'
  AND EXISTS (SELECT 1 FROM players WHERE id = 2324 AND name = 'Stefan Berg');

UPDATE players SET name = 'Stefan Berg (VH Sportbar)' WHERE id = 2324 AND name = 'Stefan Berg';

-- Bo Johansson in Hammarby 2023/2024 is another player than the one in Tyresö
UPDATE sub_match_participants SET player_id = 2335
WHERE player_id IN (1448, 1817, 2335)
  AND (SELECT CASE sub_match_participants.team_number WHEN 1 THEN t1.name ELSE t2.name END
       FROM sub_matches sm JOIN matches m ON m.id = sm.match_id
       JOIN teams t1 ON t1.id = m.team1_id JOIN teams t2 ON t2.id = m.team2_id
       WHERE sm.id = sub_match_participants.sub_match_id) LIKE 'Hammarby%'
  AND EXISTS (SELECT 1 FROM players WHERE id = 2335 AND name = 'Bo Johansson');

UPDATE players SET name = 'Bo Johansson (Hammarby)' WHERE id = 2335 AND name = 'Bo Johansson';

-- Kenneth Lundberg in Rockhangers 2024/2025 is another player than the one in Tungsten
UPDATE sub_match_participants SET player_id = 2346
WHERE player_id IN (990, 2346, 2421)
  AND (SELECT CASE sub_match_participants.team_number WHEN 1 THEN t1.name ELSE t2.name END
       FROM sub_matches sm JOIN matches m ON m.id = sm.match_id
       JOIN teams t1 ON t1.id = m.team1_id JOIN teams t2 ON t2.id = m.team2_id
       WHERE sm.id = sub_match_participants.sub_match_id) LIKE 'Rockhangers%'
  AND EXISTS (SELECT 1 FROM players WHERE id = 2346 AND name = 'Kenneth Lundberg');

UPDATE players SET name = 'Kenneth Lundberg (Rockhangers)' WHERE id = 2346 AND name = 'Kenneth Lundberg';

-- Conny Larsson's HMT Dart matches belong to the existing Conny Larsson (Hmt Dart)
UPDATE sub_match_participants SET player_id = 732
WHERE player_id IN (2320, 2321)
  AND (SELECT CASE sub_match_participants.team_number WHEN 1 THEN t1.name ELSE t2.name END
       FROM sub_matches sm JOIN matches m ON m.id = sm.match_id
       JOIN teams t1 ON t1.id = m.team1_id JOIN teams t2 ON t2.id = m.team2_id
       WHERE sm.id = sub_match_participants.sub_match_id) LIKE 'HMT%'
  AND EXISTS (SELECT 1 FROM players WHERE id = 732 AND name = 'Conny Larsson (Hmt Dart)');

-- The rest is one player per name, kept on the lowest id, which the site looks up
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 910, 857, 'Stefan Ågren', 'Samma spelare registrerad flera gånger, granskad'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 910 AND name = 'Stefan Ågren')
  AND EXISTS (SELECT 1 FROM players WHERE id = 857 AND name = 'Stefan Ågren');

INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2329, 857, 'Stefan Ågren', 'Samma spelare registrerad flera gånger, granskad'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2329 AND name = 'Stefan Ågren')
  AND EXISTS (SELECT 1 FROM players WHERE id = 857 AND name = 'Stefan Ågren');

INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2349, 695, 'Håkan Eklund', 'Samma spelare registrerad flera gånger, granskad'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2349 AND name = 'Håkan Eklund')
  AND EXISTS (SELECT 1 FROM players WHERE id = 695 AND name = 'Håkan Eklund');

INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2371, 695, 'Håkan Eklund', 'Samma spelare registrerad flera gånger, granskad'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2371 AND name = 'Håkan Eklund')
  AND EXISTS (SELECT 1 FROM players WHERE id = 695 AND name = 'Håkan Eklund');

INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1763, 100, 'Thomas Bergström', 'Samma spelare registrerad flera gånger, granskad'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1763 AND name = 'Thomas Bergström')
  AND EXISTS (SELECT 1 FROM players WHERE id = 100 AND name = 'Thomas Bergström');

INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2333, 100, 'Thomas Bergström', 'Samma spelare registrerad flera gånger, granskad'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2333 AND name = 'Thomas Bergström')
  AND EXISTS (SELECT 1 FROM players WHERE id = 100 AND name = 'Thomas Bergström');

INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2334, 100, 'Thomas Bergström', 'Samma spelare registrerad flera gånger, granskad'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2334 AND name = 'Thomas Bergström')
  AND EXISTS (SELECT 1 FROM players WHERE id = 100 AND name = 'Thomas Bergström');

INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1817, 1448, 'Bo Johansson', 'Samma spelare registrerad flera gånger, granskad'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1817 AND name = 'Bo Johansson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1448 AND name = 'Bo Johansson');

INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2421, 990, 'Kenneth Lundberg', 'Samma spelare registrerad flera gånger, granskad'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2421 AND name = 'Kenneth Lundberg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 990 AND name = 'Kenneth Lundberg');

INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2326, 303, 'Stefan Berg', 'Samma spelare registrerad flera gånger, granskad'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2326 AND name = 'Stefan Berg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 303 AND name = 'Stefan Berg');

INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2434, 303, 'Stefan Berg', 'Samma spelare registrerad flera gånger, granskad'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2434 AND name = 'Stefan Berg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 303 AND name = 'Stefan Berg');

INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2321, 2320, 'Conny Larsson', 'Samma spelare registrerad flera gånger, granskad'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2321 AND name = 'Conny Larsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2320 AND name = 'Conny Larsson');

-- Same follow-up as in 027
-- Every alias points straight at a player that is not itself an alias
UPDATE player_aliases
SET canonical_player_id = (SELECT b.canonical_player_id FROM player_aliases b
                           WHERE b.alias_player_id = player_aliases.canonical_player_id),
    canonical_player_name = (SELECT b.canonical_player_name FROM player_aliases b
                             WHERE b.alias_player_id = player_aliases.canonical_player_id)
WHERE canonical_player_id IN (SELECT alias_player_id FROM player_aliases);

-- Sub-match mappings between two ids of the same player say nothing once they are merged,
-- and would break the rule that a mapping goes to another player
DELETE FROM sub_match_player_mappings
WHERE COALESCE((SELECT canonical_player_id FROM player_aliases WHERE alias_player_id = original_player_id), original_player_id)
    = COALESCE((SELECT canonical_player_id FROM player_aliases WHERE alias_player_id = correct_player_id), correct_player_id);

-- Mappings to an alias go to the kept player, by id and by name, since the site matches on the name
UPDATE sub_match_player_mappings
SET correct_player_name = (SELECT canonical_player_name FROM player_aliases WHERE alias_player_id = correct_player_id),
    correct_player_id = (SELECT canonical_player_id FROM player_aliases WHERE alias_player_id = correct_player_id)
WHERE correct_player_id IN (SELECT alias_player_id FROM player_aliases);

-- Mappings from an alias move with its matches, unless the kept player already has one for that sub-match
DELETE FROM sub_match_player_mappings
WHERE original_player_id IN (SELECT alias_player_id FROM player_aliases)
  AND EXISTS (
      SELECT 1 FROM sub_match_player_mappings o
      WHERE o.sub_match_id = sub_match_player_mappings.sub_match_id
        AND o.original_player_id = (SELECT canonical_player_id FROM player_aliases
                                    WHERE alias_player_id = sub_match_player_mappings.original_player_id)
  );

UPDATE sub_match_player_mappings
SET original_player_id = (SELECT canonical_player_id FROM player_aliases WHERE alias_player_id = original_player_id)
WHERE original_player_id IN (SELECT alias_player_id FROM player_aliases);

UPDATE sub_match_participants
SET player_id = (SELECT canonical_player_id FROM player_aliases WHERE alias_player_id = sub_match_participants.player_id)
WHERE player_id IN (SELECT alias_player_id FROM player_aliases);
