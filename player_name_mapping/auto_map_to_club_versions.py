#!/usr/bin/env python3
"""
Automatically map generic player names to club-specific versions
based on which club they played for in each match.
"""
import sqlite3

def extract_club_name(team_name):
    """Extract club name from 'Club (Division)' format"""
    if '(' in team_name:
        return team_name.split('(')[0].strip()
    return team_name.strip()

def standardize_club_name(club_name):
    """Standardize club names to handle minor variations"""
    standardized = club_name.lower().strip()
    # Remove common suffixes
    standardized = standardized.replace(' dc', '').replace(' dart', '')
    # Fix common variations
    if 'järfälla' in standardized or 'jarfalla' in standardized:
        return 'järfalla'
    if 'tyresö' in standardized or 'tyresco' in standardized:
        return 'tyresö'
    if 'stockholm' in standardized and ('bullseye' in standardized or 'busseye' in standardized):
        return 'stockholms bullseye'
    return standardized

def auto_map_club_versions(dry_run=True):
    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()

        print("=== Auto-mapping generic players to club versions ===\n")

        # Get all generic players with club-specific versions
        cursor.execute('''
            SELECT DISTINCT p.id, p.name
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            WHERE p.name NOT LIKE '%(%'
                AND LENGTH(p.name) >= 3
                AND NOT EXISTS (
                    SELECT 1 FROM sub_match_player_mappings
                    WHERE original_player_id = p.id
                )
            ORDER BY p.name
        ''')

        generic_players = cursor.fetchall()

        total_mappings = 0
        players_mapped = 0

        for player_id, player_name in generic_players:
            # Check if club versions exist
            cursor.execute('''
                SELECT id, name
                FROM players
                WHERE name LIKE ? || ' (%'
            ''', (player_name,))

            club_versions = cursor.fetchall()

            if not club_versions:
                continue

            # Get all matches for this player with team context
            cursor.execute('''
                SELECT
                    smp.sub_match_id,
                    CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team,
                    m.season,
                    m.division
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE smp.player_id = ?
            ''', (player_id,))

            matches = cursor.fetchall()

            if not matches:
                continue

            player_had_mappings = False

            for sub_match_id, team_name, season, division in matches:
                match_club = extract_club_name(team_name)
                match_club_std = standardize_club_name(match_club)

                # Find best matching club version
                best_match = None
                best_score = 0

                for cv_id, cv_name in club_versions:
                    # Extract club from version name (e.g., "Name (Club)" -> "Club")
                    if '(' not in cv_name:
                        continue

                    version_club = cv_name.split('(')[1].rstrip(')')
                    version_club_std = standardize_club_name(version_club)

                    # Score the match
                    score = 0
                    if version_club_std == match_club_std:
                        score = 100  # Perfect match
                    elif version_club_std in match_club_std or match_club_std in version_club_std:
                        score = 80   # Partial match

                    if score > best_score:
                        best_score = score
                        best_match = (cv_id, cv_name)

                if best_match and best_score >= 80:
                    target_id, target_name = best_match
                    context = f"{team_name} ({division}) {season}"

                    if not dry_run:
                        cursor.execute('''
                            INSERT OR REPLACE INTO sub_match_player_mappings (
                                sub_match_id,
                                original_player_id,
                                correct_player_id,
                                correct_player_name,
                                match_context,
                                confidence,
                                mapping_reason,
                                notes
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            sub_match_id,
                            player_id,
                            target_id,
                            target_name,
                            context,
                            best_score,
                            f"Auto-mapped to club version based on team context",
                            f"Match club: {match_club}"
                        ))

                    total_mappings += 1
                    player_had_mappings = True

            if player_had_mappings:
                players_mapped += 1
                if dry_run:
                    print(f"[DRY RUN] Would map {player_name} (ID {player_id})")
                    for cv_id, cv_name in club_versions:
                        print(f"          -> {cv_name}")
                else:
                    print(f"Mapped {player_name} (ID {player_id}) to club versions")

        if not dry_run:
            conn.commit()
            print(f"\n=== COMPLETED ===")
            print(f"Created {total_mappings} mappings for {players_mapped} players")
        else:
            print(f"\n=== DRY RUN ===")
            print(f"Would create {total_mappings} mappings for {players_mapped} players")
            print("\nRun with --apply to create mappings")

if __name__ == "__main__":
    import sys

    if "--apply" in sys.argv:
        auto_map_club_versions(dry_run=False)
    else:
        auto_map_club_versions(dry_run=True)
