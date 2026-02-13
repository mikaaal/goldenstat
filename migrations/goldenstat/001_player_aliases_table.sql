-- Skapa player_aliases-tabell för att mappa alias-spelare till kanoniska spelare.
-- Används av smart_season_importer.resolve_player_alias() vid import.

CREATE TABLE IF NOT EXISTS player_aliases (
    alias_player_id INTEGER PRIMARY KEY,
    canonical_player_id INTEGER NOT NULL,
    canonical_player_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (alias_player_id) REFERENCES players(id),
    FOREIGN KEY (canonical_player_id) REFERENCES players(id),
    CHECK(alias_player_id != canonical_player_id)
);

-- Bernte (SpikKastarna) -> Bernth Andersson
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2304, 2352, 'Bernth Andersson', 'Bernte (SpikKastarna) är Bernth Andersson'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2304)
  AND EXISTS (SELECT 1 FROM players WHERE id = 2352);

-- Kari (Tyresö DC) -> Kari Dagudde
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2182, 2677, 'Kari Dagudde', 'Kari (Tyresö DC) är Kari Dagudde'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2182)
  AND EXISTS (SELECT 1 FROM players WHERE id = 2677);

-- Kari Dagudde (SpikKastarna) -> Kari Dagudde
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2344, 2677, 'Kari Dagudde', 'Kari Dagudde (SpikKastarna) är Kari Dagudde'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2344)
  AND EXISTS (SELECT 1 FROM players WHERE id = 2677);
