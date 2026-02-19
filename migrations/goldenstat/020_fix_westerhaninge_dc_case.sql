-- Korrigera case: "Westerhaninge Dc" -> "Westerhaninge DC"
UPDATE players SET name = REPLACE(name, 'Westerhaninge Dc)', 'Westerhaninge DC)')
WHERE name LIKE '%Westerhaninge Dc)%';
