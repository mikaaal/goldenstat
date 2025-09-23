-- Enhanced Player Name Mapping System
-- Designed to handle complex name disambiguation scenarios
-- Created: 2025-09-22

-- Main mapping table for name consolidation
CREATE TABLE IF NOT EXISTS player_name_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- The source player record that needs mapping
    source_player_id INTEGER NOT NULL,
    
    -- The target canonical player record
    target_player_id INTEGER NOT NULL,
    
    -- The canonical display name
    canonical_name TEXT NOT NULL,
    
    -- Context-specific information
    specific_context TEXT, -- e.g., "Oilers (3FC)" for team/division context
    
    -- Confidence and validation
    confidence INTEGER DEFAULT 80 CHECK (confidence BETWEEN 1 AND 100),
    validation_status TEXT DEFAULT 'pending' CHECK (validation_status IN ('pending', 'validated', 'rejected', 'needs_review')),
    
    -- Mapping type and source
    mapping_type TEXT NOT NULL CHECK (mapping_type IN (
        'simple_name_variant',      -- Case differences, abbreviations
        'first_name_only',          -- Maps "Peter" to "Peter Söron" 
        'club_context_based',       -- Based on club/team uniqueness
        'temporal_validation',      -- Based on timeline analysis
        'manual_override'           -- Manually created mapping
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
    UNIQUE(source_player_id), -- Each source can only map to one target
    CHECK(source_player_id != target_player_id) -- No self-mapping
);

-- Context validation table - tracks which contexts a player name appears in
CREATE TABLE IF NOT EXISTS player_context_validation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    club_name TEXT NOT NULL,        -- Extracted from team name
    division TEXT NOT NULL,
    season TEXT NOT NULL,
    date_range_start DATE,
    date_range_end DATE,
    match_count INTEGER DEFAULT 0,
    
    FOREIGN KEY (player_id) REFERENCES players(id),
    UNIQUE(player_id, club_name, division, season)
);

-- Temporal overlap detection table
CREATE TABLE IF NOT EXISTS temporal_overlaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player1_id INTEGER NOT NULL,
    player2_id INTEGER NOT NULL,
    overlap_start DATE NOT NULL,
    overlap_end DATE NOT NULL,
    different_clubs BOOLEAN DEFAULT FALSE,
    conflict_severity TEXT CHECK (conflict_severity IN ('low', 'medium', 'high')),
    resolution_status TEXT DEFAULT 'unresolved' CHECK (resolution_status IN ('unresolved', 'false_positive', 'real_conflict')),
    notes TEXT,
    
    FOREIGN KEY (player1_id) REFERENCES players(id),
    FOREIGN KEY (player2_id) REFERENCES players(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_player_name_mappings_source ON player_name_mappings(source_player_id);
CREATE INDEX IF NOT EXISTS idx_player_name_mappings_target ON player_name_mappings(target_player_id);
CREATE INDEX IF NOT EXISTS idx_player_name_mappings_status ON player_name_mappings(validation_status);
CREATE INDEX IF NOT EXISTS idx_context_validation_player ON player_context_validation(player_id);
CREATE INDEX IF NOT EXISTS idx_context_validation_club ON player_context_validation(club_name);
CREATE INDEX IF NOT EXISTS idx_temporal_overlaps_players ON temporal_overlaps(player1_id, player2_id);

-- View to get effective player data with all mappings applied
CREATE VIEW IF NOT EXISTS effective_player_data AS
SELECT 
    p.id as original_player_id,
    p.name as original_name,
    COALESCE(pnm.canonical_name, p.name) as display_name,
    COALESCE(pnm.target_player_id, p.id) as effective_player_id,
    pnm.mapping_type,
    pnm.confidence,
    pnm.validation_status,
    pnm.specific_context,
    CASE 
        WHEN pnm.id IS NOT NULL THEN TRUE 
        ELSE FALSE 
    END as is_mapped
FROM players p
LEFT JOIN player_name_mappings pnm ON p.id = pnm.source_player_id 
    AND pnm.validation_status IN ('validated', 'pending');

-- View to identify players that need disambiguation
CREATE VIEW IF NOT EXISTS players_needing_disambiguation AS
SELECT 
    p.name,
    COUNT(*) as player_count,
    GROUP_CONCAT(DISTINCT p.id) as player_ids,
    MIN(LENGTH(p.name)) as shortest_name_length,
    MAX(LENGTH(p.name)) as longest_name_length
FROM players p
LEFT JOIN player_name_mappings pnm ON p.id = pnm.source_player_id
WHERE pnm.id IS NULL  -- Not already mapped
GROUP BY p.name
HAVING COUNT(*) > 1
ORDER BY player_count DESC, LENGTH(p.name);