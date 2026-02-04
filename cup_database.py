import sqlite3
import os
from typing import Optional, Dict, Any


class CupDatabase:
    def __init__(self, db_path: str = "cups.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with schema if tables don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tournaments'")
            if not cursor.fetchone():
                self._create_schema(conn)

            # Always ensure cup_player_mappings exists (added later)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cup_player_mappings'")
            if not cursor.fetchone():
                conn.executescript("""
                    CREATE TABLE cup_player_mappings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alias_player_id INTEGER NOT NULL UNIQUE,
                        canonical_player_id INTEGER NOT NULL,
                        alias_name TEXT NOT NULL,
                        canonical_name TEXT NOT NULL,
                        mapping_reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (alias_player_id) REFERENCES players(id),
                        FOREIGN KEY (canonical_player_id) REFERENCES players(id),
                        CHECK(alias_player_id != canonical_player_id)
                    );
                    CREATE INDEX idx_cup_player_mappings_alias ON cup_player_mappings(alias_player_id);
                    CREATE INDEX idx_cup_player_mappings_canonical ON cup_player_mappings(canonical_player_id);
                """)

    def _create_schema(self, conn):
        """Create the initial database schema"""
        conn.executescript("""
                CREATE TABLE tournaments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tdid VARCHAR(50) NOT NULL UNIQUE,
                    title VARCHAR(255) NOT NULL,
                    tournament_date TIMESTAMP,
                    status INTEGER,
                    team_games INTEGER NOT NULL DEFAULT 0,
                    lgid VARCHAR(50),
                    start_score INTEGER DEFAULT 501,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tournament_id INTEGER NOT NULL,
                    tpid VARCHAR(50) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    start_score INTEGER,
                    FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
                    UNIQUE(tournament_id, tpid)
                );

                CREATE TABLE players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE participant_players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    participant_id INTEGER NOT NULL,
                    player_id INTEGER NOT NULL,
                    FOREIGN KEY (participant_id) REFERENCES participants(id),
                    FOREIGN KEY (player_id) REFERENCES players(id),
                    UNIQUE(participant_id, player_id)
                );

                CREATE TABLE cup_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tournament_id INTEGER NOT NULL,
                    phase VARCHAR(10) NOT NULL,
                    phase_detail VARCHAR(50),
                    participant1_id INTEGER NOT NULL,
                    participant2_id INTEGER NOT NULL,
                    p1_legs_won INTEGER DEFAULT 0,
                    p2_legs_won INTEGER DEFAULT 0,
                    p1_average REAL,
                    p2_average REAL,
                    tmid VARCHAR(255),
                    has_detail INTEGER DEFAULT 0,
                    FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
                    FOREIGN KEY (participant1_id) REFERENCES participants(id),
                    FOREIGN KEY (participant2_id) REFERENCES participants(id),
                    UNIQUE(tournament_id, tmid)
                );

                CREATE TABLE legs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cup_match_id INTEGER NOT NULL,
                    leg_number INTEGER NOT NULL,
                    winner_side INTEGER NOT NULL,
                    first_side INTEGER NOT NULL,
                    total_rounds INTEGER NOT NULL,
                    FOREIGN KEY (cup_match_id) REFERENCES cup_matches(id)
                );

                CREATE TABLE throws (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    leg_id INTEGER NOT NULL,
                    side_number INTEGER NOT NULL,
                    round_number INTEGER NOT NULL,
                    score INTEGER NOT NULL,
                    remaining_score INTEGER NOT NULL,
                    darts_used INTEGER,
                    FOREIGN KEY (leg_id) REFERENCES legs(id)
                );

                CREATE INDEX idx_participants_tournament ON participants(tournament_id);
                CREATE INDEX idx_participant_players_participant ON participant_players(participant_id);
                CREATE INDEX idx_participant_players_player ON participant_players(player_id);
                CREATE INDEX idx_cup_matches_tournament ON cup_matches(tournament_id);
                CREATE INDEX idx_cup_matches_phase ON cup_matches(tournament_id, phase);
                CREATE INDEX idx_legs_cup_match ON legs(cup_match_id);
                CREATE INDEX idx_throws_leg ON throws(leg_id);
                CREATE INDEX idx_players_name ON players(name);
        """)
        conn.commit()

    def get_or_create_tournament(self, data: Dict[str, Any]) -> Optional[int]:
        """Get existing tournament by tdid or create new one. Returns id or None if already exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tournaments WHERE tdid = ?", (data['tdid'],))
            result = cursor.fetchone()
            if result:
                return result[0]

            cursor.execute("""
                INSERT INTO tournaments (tdid, title, tournament_date, status, team_games, lgid, start_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data['tdid'],
                data['title'],
                data.get('tournament_date'),
                data.get('status'),
                data.get('team_games', 0),
                data.get('lgid'),
                data.get('start_score', 501),
            ))
            return cursor.lastrowid

    def get_or_create_participant(self, tournament_id: int, tpid: str, name: str, start_score: int = None) -> int:
        """Get existing participant or create new one. Returns participant id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM participants WHERE tournament_id = ? AND tpid = ?",
                (tournament_id, tpid)
            )
            result = cursor.fetchone()
            if result:
                return result[0]

            cursor.execute("""
                INSERT INTO participants (tournament_id, tpid, name, start_score)
                VALUES (?, ?, ?, ?)
            """, (tournament_id, tpid, name, start_score))
            return cursor.lastrowid

    @staticmethod
    def _capitalize_word(word: str) -> str:
        """Capitalize a single word, handling hyphens and quotes."""
        # Hyphenated names: Per-Erik, not Per-erik
        if '-' in word:
            return '-'.join(part.capitalize() for part in word.split('-'))
        # Quoted nicknames: keep as-is (e.g. "Bacon")
        if word.startswith('"') and word.endswith('"'):
            inner = word[1:-1]
            return f'"{inner.capitalize()}"'
        return word.capitalize()

    @staticmethod
    def normalize_player_name(name: str) -> str:
        """Normalize player name to title case to avoid duplicates from ALL CAPS entries.
        Preserves parenthesized content (club abbreviations) and handles hyphens."""
        if not name:
            return name

        name = name.strip()

        # Handle parenthesized suffix: "DANIEL LARSSON (SSDC)" -> name + club kept as-is
        if '(' in name and ')' in name:
            paren_start = name.index('(')
            paren_end = name.rindex(')')
            before = name[:paren_start].strip()
            paren_content = name[paren_start:paren_end + 1]  # includes parens
            after = name[paren_end + 1:].strip()

            normalized_before = ' '.join(
                CupDatabase._capitalize_word(w) for w in before.split() if w
            )
            # Keep parenthesized content as-is (club abbreviations)
            parts = [normalized_before, paren_content]
            if after:
                parts.append(' '.join(
                    CupDatabase._capitalize_word(w) for w in after.split() if w
                ))
            return ' '.join(parts)

        return ' '.join(CupDatabase._capitalize_word(w) for w in name.split() if w)

    def get_or_create_player(self, name: str) -> int:
        """Get existing player by name or create new one. Returns player id.
        If the player is a known alias, returns the canonical player instead."""
        normalized = self.normalize_player_name(name)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM players WHERE name = ?", (normalized,))
            result = cursor.fetchone()
            if result:
                player_id = result[0]
                # Check if this player is an alias for another (canonical) player
                cursor.execute(
                    "SELECT canonical_player_id FROM cup_player_mappings WHERE alias_player_id = ?",
                    (player_id,)
                )
                mapping = cursor.fetchone()
                if mapping:
                    return mapping[0]
                return player_id

            cursor.execute("INSERT INTO players (name) VALUES (?)", (normalized,))
            return cursor.lastrowid

    def link_participant_player(self, participant_id: int, player_id: int):
        """Link a participant to a player. Skips if already linked."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM participant_players WHERE participant_id = ? AND player_id = ?",
                (participant_id, player_id)
            )
            if cursor.fetchone():
                return
            cursor.execute(
                "INSERT INTO participant_players (participant_id, player_id) VALUES (?, ?)",
                (participant_id, player_id)
            )

    def get_participant_by_tpid(self, tournament_id: int, tpid: str) -> Optional[int]:
        """Get participant id by tournament and tpid."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM participants WHERE tournament_id = ? AND tpid = ?",
                (tournament_id, tpid)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def insert_cup_match(self, data: Dict[str, Any]) -> Optional[int]:
        """Insert a cup match. Returns match id, or existing id if tmid already exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if data.get('tmid'):
                cursor.execute(
                    "SELECT id FROM cup_matches WHERE tournament_id = ? AND tmid = ?",
                    (data['tournament_id'], data['tmid'])
                )
                result = cursor.fetchone()
                if result:
                    return result[0]

            cursor.execute("""
                INSERT INTO cup_matches
                (tournament_id, phase, phase_detail, participant1_id, participant2_id,
                 p1_legs_won, p2_legs_won, p1_average, p2_average, tmid, has_detail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['tournament_id'],
                data['phase'],
                data.get('phase_detail'),
                data['participant1_id'],
                data['participant2_id'],
                data.get('p1_legs_won', 0),
                data.get('p2_legs_won', 0),
                data.get('p1_average'),
                data.get('p2_average'),
                data.get('tmid'),
                data.get('has_detail', 0),
            ))
            return cursor.lastrowid

    def insert_leg(self, data: Dict[str, Any]) -> int:
        """Insert a leg and return its id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO legs (cup_match_id, leg_number, winner_side, first_side, total_rounds)
                VALUES (?, ?, ?, ?, ?)
            """, (
                data['cup_match_id'],
                data['leg_number'],
                data['winner_side'],
                data['first_side'],
                data['total_rounds'],
            ))
            return cursor.lastrowid

    def insert_throw(self, data: Dict[str, Any]):
        """Insert a throw."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO throws (leg_id, side_number, round_number, score, remaining_score, darts_used)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data['leg_id'],
                data['side_number'],
                data['round_number'],
                data['score'],
                data['remaining_score'],
                data.get('darts_used'),
            ))

    def mark_match_has_detail(self, match_id: int):
        """Mark a cup_match as having detail data fetched."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE cup_matches SET has_detail = 1 WHERE id = ?", (match_id,))
            conn.commit()

    def get_canonical_player_id(self, player_id: int) -> int:
        """If player_id is an alias, return the canonical player id. Otherwise return the same id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT canonical_player_id FROM cup_player_mappings WHERE alias_player_id = ?",
                (player_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else player_id

    def is_alias_player(self, player_id: int) -> bool:
        """Check if a player_id is an alias (mapped to another canonical player)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM cup_player_mappings WHERE alias_player_id = ?",
                (player_id,)
            )
            return cursor.fetchone() is not None

    def get_matches_without_detail(self, tournament_id: int):
        """Get all cup_matches that haven't had detail data fetched yet."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cm.id, cm.tmid, cm.phase, cm.phase_detail,
                       p1.tpid as p1_tpid, p2.tpid as p2_tpid
                FROM cup_matches cm
                JOIN participants p1 ON cm.participant1_id = p1.id
                JOIN participants p2 ON cm.participant2_id = p2.id
                WHERE cm.tournament_id = ? AND cm.has_detail = 0 AND cm.tmid IS NOT NULL
            """, (tournament_id,))
            return [dict(row) for row in cursor.fetchall()]
