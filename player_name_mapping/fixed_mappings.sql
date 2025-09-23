-- Fixed Peter mappings - remove UNIQUE constraint on source_player_id
-- This allows multiple mappings from the same source player to different targets

CREATE TABLE IF NOT EXISTS player_name_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_player_id INTEGER NOT NULL,
    target_player_id INTEGER NOT NULL,
    canonical_name TEXT NOT NULL,
    specific_context TEXT,
    confidence INTEGER DEFAULT 80 CHECK (confidence BETWEEN 1 AND 100),
    validation_status TEXT DEFAULT 'pending' CHECK (validation_status IN ('pending', 'validated', 'rejected', 'needs_review')),
    mapping_type TEXT NOT NULL CHECK (mapping_type IN (
        'simple_name_variant',
        'first_name_only',
        'club_context_based',
        'temporal_validation',
        'manual_override'
    )),
    club_uniqueness_validated BOOLEAN DEFAULT FALSE,
    temporal_uniqueness_validated BOOLEAN DEFAULT FALSE,
    created_by TEXT DEFAULT 'system',
    reviewed_by TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    
    -- Constraints - REMOVED unique constraint on source_player_id
    FOREIGN KEY (source_player_id) REFERENCES players(id),
    FOREIGN KEY (target_player_id) REFERENCES players(id),
    CHECK(source_player_id != target_player_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_player_name_mappings_source ON player_name_mappings(source_player_id);
CREATE INDEX IF NOT EXISTS idx_player_name_mappings_target ON player_name_mappings(target_player_id);
CREATE INDEX IF NOT EXISTS idx_player_name_mappings_status ON player_name_mappings(validation_status);

-- Insert all Peter mappings
INSERT INTO player_name_mappings (
    source_player_id, target_player_id, canonical_name, specific_context,
    confidence, mapping_type, validation_status, club_uniqueness_validated,
    temporal_uniqueness_validated, notes
) VALUES 
(386, 552, 'Peter Book', 'Oilers context matches', 95, 'first_name_only', 'validated', 1, 1, '28 matches mapped from Peter to Peter Book'),
(386, 838, 'Peter Söron', 'Oasen context matches', 95, 'first_name_only', 'validated', 1, 1, '47 matches mapped from Peter to Peter Söron'),
(386, 1967, 'Peter Palm', 'Lärkan context matches', 90, 'first_name_only', 'validated', 1, 1, '1 match mapped from Peter to Peter Palm'),
(386, 884, 'Peter Aland', 'Dartanjang context matches', 95, 'first_name_only', 'validated', 1, 1, '4 matches mapped from Peter to Peter Aland'),
(386, 19, 'Peter Vahlner', 'Sweden Capital context matches', 50, 'first_name_only', 'validated', 1, 1, '35 matches mapped from Peter to Peter Vahlner'),
(386, 766, 'Peter Ekman', 'Bålsta context matches', 95, 'first_name_only', 'validated', 1, 1, '4 matches mapped from Peter to Peter Ekman');

-- Verify the mappings
SELECT 
    pnm.id,
    p_source.name as source_name,
    p_target.name as target_name,
    pnm.confidence,
    pnm.specific_context
FROM player_name_mappings pnm
JOIN players p_source ON pnm.source_player_id = p_source.id
JOIN players p_target ON pnm.target_player_id = p_target.id
ORDER BY pnm.confidence DESC;