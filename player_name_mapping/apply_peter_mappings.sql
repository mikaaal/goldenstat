-- Apply Peter name mappings to database
-- This will create the mapping table and insert the Peter mappings

-- First create the mapping table structure
CREATE TABLE IF NOT EXISTS player_name_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- The source player record that needs mapping
    source_player_id INTEGER NOT NULL,
    
    -- The target canonical player record
    target_player_id INTEGER NOT NULL,
    
    -- The canonical display name
    canonical_name TEXT NOT NULL,
    
    -- Context-specific information
    specific_context TEXT,
    
    -- Confidence and validation
    confidence INTEGER DEFAULT 80 CHECK (confidence BETWEEN 1 AND 100),
    validation_status TEXT DEFAULT 'pending' CHECK (validation_status IN ('pending', 'validated', 'rejected', 'needs_review')),
    
    -- Mapping type and source
    mapping_type TEXT NOT NULL CHECK (mapping_type IN (
        'simple_name_variant',
        'first_name_only',
        'club_context_based',
        'temporal_validation',
        'manual_override'
    )),
    
    -- Validation criteria met
    club_uniqueness_validated BOOLEAN DEFAULT FALSE,
    temporal_uniqueness_validated BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_by TEXT DEFAULT 'system',
    reviewed_by TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    
    -- Constraints
    FOREIGN KEY (source_player_id) REFERENCES players(id),
    FOREIGN KEY (target_player_id) REFERENCES players(id),
    UNIQUE(source_player_id),
    CHECK(source_player_id != target_player_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_player_name_mappings_source ON player_name_mappings(source_player_id);
CREATE INDEX IF NOT EXISTS idx_player_name_mappings_target ON player_name_mappings(target_player_id);
CREATE INDEX IF NOT EXISTS idx_player_name_mappings_status ON player_name_mappings(validation_status);

-- Now apply the Peter mappings
INSERT OR REPLACE INTO player_name_mappings (
    source_player_id, 
    target_player_id, 
    canonical_name, 
    specific_context,
    confidence, 
    mapping_type, 
    validation_status,
    club_uniqueness_validated,
    temporal_uniqueness_validated,
    notes
) VALUES (
    386, 
    552, 
    'Peter Book',
    'Oilers (3FC) 2023/2024',
    95, 
    'first_name_only', 
    'validated',
    1,
    1,
    'Auto-mapped from Peter based on: same_club, same_season, similar_club (confidence: 105)'
);

INSERT OR REPLACE INTO player_name_mappings (
    source_player_id, 
    target_player_id, 
    canonical_name, 
    specific_context,
    confidence, 
    mapping_type, 
    validation_status,
    club_uniqueness_validated,
    temporal_uniqueness_validated,
    notes
) VALUES (
    386, 
    838, 
    'Peter Söron',
    'Oasen (3FD) 2023/2024',
    95, 
    'first_name_only', 
    'validated',
    1,
    1,
    'Auto-mapped from Peter based on: same_club, same_season, similar_club (confidence: 95)'
);

INSERT OR REPLACE INTO player_name_mappings (
    source_player_id, 
    target_player_id, 
    canonical_name, 
    specific_context,
    confidence, 
    mapping_type, 
    validation_status,
    club_uniqueness_validated,
    temporal_uniqueness_validated,
    notes
) VALUES (
    386, 
    1967, 
    'Peter Palm',
    'Lärkan (2FA) 2023/2024',
    90, 
    'first_name_only', 
    'validated',
    1,
    1,
    'Auto-mapped from Peter based on: same_club, same_season, same_division (confidence: 90)'
);

INSERT OR REPLACE INTO player_name_mappings (
    source_player_id, 
    target_player_id, 
    canonical_name, 
    specific_context,
    confidence, 
    mapping_type, 
    validation_status,
    club_uniqueness_validated,
    temporal_uniqueness_validated,
    notes
) VALUES (
    386, 
    884, 
    'Peter Aland',
    'Dartanjang (Superligan) (Superligan) 2023/2024',
    95, 
    'first_name_only', 
    'validated',
    1,
    1,
    'Auto-mapped from Peter based on: same_club, same_season, similar_club (confidence: 95)'
);

INSERT OR REPLACE INTO player_name_mappings (
    source_player_id, 
    target_player_id, 
    canonical_name, 
    specific_context,
    confidence, 
    mapping_type, 
    validation_status,
    club_uniqueness_validated,
    temporal_uniqueness_validated,
    notes
) VALUES (
    386, 
    19, 
    'Peter Vahlner',
    'Sweden Capital (3A) 2023/2024',
    50, 
    'first_name_only', 
    'validated',
    1,
    1,
    'Auto-mapped from Peter based on: same_season, same_division (confidence: 50)'
);

INSERT OR REPLACE INTO player_name_mappings (
    source_player_id, 
    target_player_id, 
    canonical_name, 
    specific_context,
    confidence, 
    mapping_type, 
    validation_status,
    club_uniqueness_validated,
    temporal_uniqueness_validated,
    notes
) VALUES (
    386, 
    766, 
    'Peter Ekman',
    'Bålsta (SL6) (SL6) 2024/2025',
    95, 
    'first_name_only', 
    'validated',
    1,
    1,
    'Auto-mapped from Peter based on: same_club, same_season, similar_club (confidence: 95)'
);

-- Verify the mappings were created
SELECT 
    pnm.id,
    p_source.name as source_name,
    p_target.name as target_name,
    pnm.confidence,
    pnm.specific_context
FROM player_name_mappings pnm
JOIN players p_source ON pnm.source_player_id = p_source.id
JOIN players p_target ON pnm.target_player_id = p_target.id
WHERE p_source.name = 'Peter'
ORDER BY pnm.confidence DESC;