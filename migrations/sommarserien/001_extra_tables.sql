-- Tabeller som behövs av SmartSeasonImporter men som inte ingår i basSchemat.
-- Appliceras en gång vid bootstrapping av sommarserien.db.

CREATE TABLE IF NOT EXISTS sub_match_player_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sub_match_id INTEGER NOT NULL,
    original_player_id INTEGER NOT NULL,
    correct_player_id INTEGER NOT NULL,
    correct_player_name TEXT NOT NULL,
    match_context TEXT,
    confidence INTEGER DEFAULT 80 CHECK (confidence BETWEEN 1 AND 100),
    mapping_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (sub_match_id) REFERENCES sub_matches(id),
    FOREIGN KEY (original_player_id) REFERENCES players(id),
    FOREIGN KEY (correct_player_id) REFERENCES players(id),
    UNIQUE(sub_match_id, original_player_id),
    CHECK(original_player_id != correct_player_id)
);

CREATE INDEX IF NOT EXISTS idx_smp_sub_match  ON sub_match_player_mappings(sub_match_id);
CREATE INDEX IF NOT EXISTS idx_smp_original   ON sub_match_player_mappings(original_player_id);
CREATE INDEX IF NOT EXISTS idx_smp_correct    ON sub_match_player_mappings(correct_player_id);

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
