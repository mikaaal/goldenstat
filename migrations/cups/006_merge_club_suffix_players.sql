-- Players registered with their club in parentheses, e.g. "Linus Dellby (Bålsta Dart Club)",
-- become the same player as the name without the club. The import strips the club from now on
-- (CupDatabase.normalize_player_name), so this uses the same rule: everything from the first
-- "(" is dropped when at least two words are left.

CREATE TEMP TABLE club_suffix AS
SELECT id, name, trim(substr(name, 1, instr(name, '(') - 1)) AS base
FROM players
WHERE instr(name, '(') > 0
  AND instr(trim(substr(name, 1, instr(name, '(') - 1)), ' ') > 0
  AND id NOT IN (SELECT alias_player_id FROM cup_player_mappings);

-- Where nobody has the name without the club, the first such player takes it over
UPDATE players SET name = (SELECT base FROM club_suffix s WHERE s.id = players.id)
WHERE id IN (
    SELECT min(s.id) FROM club_suffix s
    WHERE NOT EXISTS (SELECT 1 FROM players p WHERE p.name = s.base)
    GROUP BY s.base
);

-- The rest become aliases of the player with the plain name, or of that player's canonical
INSERT OR IGNORE INTO cup_player_mappings
    (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT s.id,
       COALESCE(m.canonical_player_id, p.id),
       s.name,
       COALESCE(m.canonical_name, p.name),
       'club_suffix'
FROM club_suffix s
JOIN players p ON p.id = (SELECT min(id) FROM players WHERE name = s.base AND id != s.id)
LEFT JOIN cup_player_mappings m ON m.alias_player_id = p.id
WHERE (SELECT name FROM players WHERE id = s.id) != s.base;

DROP TABLE club_suffix;
