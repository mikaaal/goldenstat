-- Player mapping table for handling duplicate/variant player names
-- Created: 2025-09-19

CREATE TABLE IF NOT EXISTS player_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- The player ID that should be replaced/mapped FROM
    source_player_id INTEGER NOT NULL,
    
    -- The player ID that should be used instead (the "correct" one)
    target_player_id INTEGER NOT NULL,
    
    -- The canonical name that should be displayed (usually target player's name)
    canonical_name TEXT NOT NULL,
    
    -- Confidence level of this mapping (1-100)
    confidence INTEGER DEFAULT 80,
    
    -- Status: 'suggested', 'confirmed', 'rejected' 
    status TEXT DEFAULT 'suggested' CHECK (status IN ('suggested', 'confirmed', 'rejected')),
    
    -- What type of duplicate this was detected as
    mapping_type TEXT DEFAULT 'manual' CHECK (mapping_type IN ('case_difference', 'high_similarity', 'substring_match', 'first_name_only', 'manual')),
    
    -- Who created/approved this mapping
    created_by TEXT DEFAULT 'system',
    approved_by TEXT DEFAULT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Optional notes
    notes TEXT,
    
    -- Foreign key constraints
    FOREIGN KEY (source_player_id) REFERENCES players(id),
    FOREIGN KEY (target_player_id) REFERENCES players(id),
    
    -- Ensure no duplicate mappings
    UNIQUE(source_player_id),
    
    -- Prevent circular mappings
    CHECK(source_player_id != target_player_id)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_player_mappings_source ON player_mappings(source_player_id);
CREATE INDEX IF NOT EXISTS idx_player_mappings_target ON player_mappings(target_player_id);
CREATE INDEX IF NOT EXISTS idx_player_mappings_status ON player_mappings(status);

-- View to get effective player names (with mappings applied)
CREATE VIEW IF NOT EXISTS effective_players AS
SELECT 
    p.id,
    COALESCE(pm.canonical_name, p.name) as effective_name,
    p.name as original_name,
    CASE 
        WHEN pm.id IS NOT NULL THEN pm.target_player_id 
        ELSE p.id 
    END as effective_player_id,
    pm.mapping_type,
    pm.confidence,
    pm.status as mapping_status
FROM players p
LEFT JOIN player_mappings pm ON p.id = pm.source_player_id 
    AND pm.status = 'confirmed';