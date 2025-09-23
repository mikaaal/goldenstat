-- Sub-match level mapping approach
-- Instead of mapping entire player IDs, we map specific sub_matches to the correct player

-- Drop the current approach
DROP TABLE IF EXISTS player_name_mappings;

-- Create sub-match level mapping table
CREATE TABLE IF NOT EXISTS sub_match_player_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- The specific sub_match that needs remapping
    sub_match_id INTEGER NOT NULL,
    
    -- The original player ID in that sub_match (should be "Peter" = 386)
    original_player_id INTEGER NOT NULL,
    
    -- The correct player this sub_match should belong to
    correct_player_id INTEGER NOT NULL,
    correct_player_name TEXT NOT NULL,
    
    -- Context and confidence
    match_context TEXT, -- "Oilers (3FC) 2023/2024"
    confidence INTEGER DEFAULT 80 CHECK (confidence BETWEEN 1 AND 100),
    mapping_reason TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    
    -- Constraints
    FOREIGN KEY (sub_match_id) REFERENCES sub_matches(id),
    FOREIGN KEY (original_player_id) REFERENCES players(id),
    FOREIGN KEY (correct_player_id) REFERENCES players(id),
    UNIQUE(sub_match_id, original_player_id), -- Each sub_match can only be remapped once per original player
    CHECK(original_player_id != correct_player_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_sub_match_mappings_sub_match ON sub_match_player_mappings(sub_match_id);
CREATE INDEX IF NOT EXISTS idx_sub_match_mappings_original ON sub_match_player_mappings(original_player_id);
CREATE INDEX IF NOT EXISTS idx_sub_match_mappings_correct ON sub_match_player_mappings(correct_player_id);

-- Let's see what sub_matches we need to map by examining the Peter context
SELECT 'Current Peter sub_matches by context:' as info;

SELECT 
    sm.id as sub_match_id,
    t.name as team_name,
    m.division,
    m.season,
    m.match_date,
    COUNT(*) as sub_matches
FROM sub_match_participants smp
JOIN sub_matches sm ON smp.sub_match_id = sm.id
JOIN matches m ON sm.match_id = m.id
JOIN teams t ON (CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END) = t.id
WHERE smp.player_id = 386  -- Peter
GROUP BY t.name, m.division, m.season
ORDER BY COUNT(*) DESC
LIMIT 10;