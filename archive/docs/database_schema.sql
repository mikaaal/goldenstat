-- GoldenStat Database Schema
-- Dart statistics tracking system

-- Teams table
CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    division VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Players table  
CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Matches table - represents a full team match (seriematch)
CREATE TABLE matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_url VARCHAR(500) NOT NULL,
    team1_id INTEGER NOT NULL,
    team2_id INTEGER NOT NULL,
    team1_score INTEGER NOT NULL, -- Total legs won by team1
    team2_score INTEGER NOT NULL, -- Total legs won by team2
    team1_avg DECIMAL(5,2), -- Team average
    team2_avg DECIMAL(5,2), -- Team average
    division VARCHAR(255),
    season VARCHAR(255),
    match_date TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team1_id) REFERENCES teams(id),
    FOREIGN KEY (team2_id) REFERENCES teams(id)
);

-- Sub-matches table - represents individual matches within a team match
CREATE TABLE sub_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    match_number INTEGER NOT NULL, -- 1-10 (position in the team match)
    match_type VARCHAR(50) NOT NULL, -- 'Singles' or 'Doubles'  
    match_name VARCHAR(100), -- e.g. 'Singles1', 'Doubles2', 'AD'
    team1_legs INTEGER NOT NULL, -- Legs won by team1
    team2_legs INTEGER NOT NULL, -- Legs won by team2
    team1_avg DECIMAL(5,2), -- Average for team1 players in this sub-match
    team2_avg DECIMAL(5,2), -- Average for team2 players in this sub-match
    mid VARCHAR(255), -- Match ID for detailed data URL
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES matches(id)
);

-- Sub-match participants - links players to sub-matches
CREATE TABLE sub_match_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sub_match_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    team_number INTEGER NOT NULL, -- 1 or 2 (which team)
    player_avg DECIMAL(5,2), -- Individual player average for this sub-match
    FOREIGN KEY (sub_match_id) REFERENCES sub_matches(id),
    FOREIGN KEY (player_id) REFERENCES players(id)
);

-- Legs table - individual legs within a sub-match
CREATE TABLE legs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sub_match_id INTEGER NOT NULL,
    leg_number INTEGER NOT NULL, -- Sequential number within the sub-match
    winner_team INTEGER NOT NULL, -- 1 or 2
    first_player_team INTEGER NOT NULL, -- Which team started (1 or 2)
    total_rounds INTEGER NOT NULL, -- How many rounds the leg lasted
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sub_match_id) REFERENCES sub_matches(id)
);

-- Throws table - individual throw data
CREATE TABLE throws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    leg_id INTEGER NOT NULL,
    team_number INTEGER NOT NULL, -- 1 or 2
    round_number INTEGER NOT NULL, -- Round within the leg
    score INTEGER NOT NULL, -- Points scored in this throw
    remaining_score INTEGER NOT NULL, -- Points left after this throw
    darts_used INTEGER, -- Number of darts used (negative values indicate checkout)
    FOREIGN KEY (leg_id) REFERENCES legs(id)
);

-- Indexes for better query performance
CREATE INDEX idx_matches_teams ON matches(team1_id, team2_id);
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_sub_matches_match ON sub_matches(match_id);
CREATE INDEX idx_participants_player ON sub_match_participants(player_id);
CREATE INDEX idx_participants_sub_match ON sub_match_participants(sub_match_id);
CREATE INDEX idx_legs_sub_match ON legs(sub_match_id);
CREATE INDEX idx_throws_leg ON throws(leg_id);
CREATE INDEX idx_players_name ON players(name);