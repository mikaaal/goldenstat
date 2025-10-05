#!/usr/bin/env python3
"""
League-based Player Mapping
Uses official league data as ground truth for creating safe mappings

Created: 2025-09-21
"""
import sqlite3
import sys
from difflib import SequenceMatcher
from player_mapping_manager import PlayerMappingManager

class LeagueBasedMapper:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.mapping_manager = PlayerMappingManager(db_path)
        
        # Official names from STDF 2024/2025 Division 3A
        self.official_3a_players = [
            'Tobias Alsiö', 'Jan Zwierzak', 'Kaj Hänninen', 'Kent Molinder', 
            'Jonas Linden', 'Hans Christer Brandholdt Pedersen', 'Krister Mandahl',
            'Claes Fredrik Lavesson', 'Aron Gyulai Farkas', 'Åsa Jonsson',
            'Anders Mårtensson', 'Bengt Persson', 'Andreas Jonsson', 'Peo Edvinsson',
            'Mikael Lundberg', 'Robin Bodin', 'Mats Andersson', 'Peter Aland',
            'Jocke Olsson', 'Gareth Young', 'John Uppfeldt', 'Anders Mars-Engvall',
            'Martin Nordlöf', 'Jesper Urheim', 'Freddie Rastehed'
        ]
        
        # Official names from STDF 2024/2025 Division 1FB  
        self.official_1fb_players = [
            # SSDC
            'Johan Engström', 'Marcus Elffors', 'Tommy Pilblad', 'Markus Korhonen',
            'Richard Hagel', 'Philip Blenk', 'Patrik Kuska', 'Torbjörn Dahlgren',
            'Lars-Erik Karlsson', 'Seved Rosén', 'Andrée Bomander', 'Kenneth Högvall',
            'Kristian Thålin',
            # Nynäshamn
            'Magnus Jansson', 'Ville Jansson', 'Christoffer Grönlund', 'Ben Bodin',
            'Mathias Åström', 'Susianne Hägvall', 'Jonas Andersson',
            # Nacka Wermdö
            'Jarkko Pyykönen', 'Richard Good', 'Per Fransson', 'Mikael Kortesalmi',
            'Mikael Wetter', 'Robert Brännström', 'Micael Sandell', 'Ronny Sjölund',
            # DK Pilo  
            'Stefan Nordström', 'Tommy Jonsén', 'Eero Tikka', 'Eilert Lignell',
            'Johan Krig', 'Miguel Gonzalez', 'Gunnar Bergström'
        ]
        
        # Division 3A teams
        self.div_3a_teams = [
            'Dartanjang', 'Elektroflyers', 'Steel Tons', 'DK Pilo', 
            'AIK Dartförening', 'Pewter Tankard', 'Cobra DC', 'Mjölner',
            'Bålsta', 'Järfalla', 'Hammarby'
        ]
        
        # Division 1FB teams
        self.div_1fb_teams = [
            'SSDC', 'Nynäshamn', 'Nacka Wermdö', 'DK Pilo'
        ]
    
    def get_player_teams(self, player_name):
        """Get all teams a player has played for"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT t.name as team_name
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                WHERE p.name = ?
                ORDER BY team_name
            """, (player_name,))
            return [row[0] for row in cursor.fetchall()]
    
    def find_similar_names_in_teams(self, official_name, target_teams, min_similarity=0.8):
        """Find similar names in specific teams"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all players from target teams
            team_placeholders = ','.join(['?' for _ in target_teams])
            cursor.execute(f"""
                SELECT DISTINCT p.id, p.name, t.name as team_name
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                WHERE t.name IN ({team_placeholders})
                AND p.name != ?
            """, target_teams + [official_name])
            
            similar_players = []
            for player_id, player_name, team_name in cursor.fetchall():
                similarity = SequenceMatcher(None, 
                    official_name.lower().strip(), 
                    player_name.lower().strip()
                ).ratio()
                
                if similarity >= min_similarity:
                    similar_players.append({
                        'player_id': player_id,
                        'player_name': player_name,
                        'team_name': team_name,
                        'similarity': similarity,
                        'official_name': official_name
                    })
            
            return sorted(similar_players, key=lambda x: x['similarity'], reverse=True)
    
    def find_team_for_official_player(self, official_name):
        """Try to determine which 3A team an official player belongs to"""
        # First check if the exact name exists and which teams they play for
        teams = self.get_player_teams(official_name)
        
        # Filter for 3A teams
        matching_3a_teams = []
        for team in teams:
            for div_team in self.div_3a_teams:
                if div_team.lower() in team.lower():
                    matching_3a_teams.append(team)
        
        return matching_3a_teams
    
    def create_safe_mappings(self, dry_run=True, min_similarity=0.85):
        """Create mappings based on league context"""
        print(f"🔍 Analyzing official 3A players for safe mappings...")
        print(f"   Minimum similarity: {min_similarity}")
        print(f"   Dry run: {dry_run}")
        print()
        
        mappings_created = 0
        mappings_found = 0
        
        for official_name in self.official_3a_players:
            print(f"🔸 Analyzing: {official_name}")
            
            # Find which 3A teams this player is associated with
            player_teams = self.find_team_for_official_player(official_name)
            
            if not player_teams:
                print(f"   ⚠️  No team associations found in database")
                continue
            
            print(f"   Teams: {', '.join(player_teams)}")
            
            # Find similar names in those teams
            similar_players = self.find_similar_names_in_teams(
                official_name, player_teams, min_similarity
            )
            
            if not similar_players:
                print(f"   ✅ No similar names found (already correct)")
                continue
            
            mappings_found += len(similar_players)
            
            for similar in similar_players:
                print(f"   🎯 Found similar: '{similar['player_name']}' (similarity: {similar['similarity']:.2f})")
                print(f"      Team: {similar['team_name']}")
                
                if not dry_run:
                    # Check if mapping already exists
                    existing_mappings = self.mapping_manager.list_suggestions('confirmed')
                    source_already_mapped = any(
                        m['source_name'] == similar['player_name'] 
                        for m in existing_mappings
                    )
                    
                    if source_already_mapped:
                        print(f"      ⏭️  Already mapped")
                        continue
                    
                    # Create mapping
                    mapping_type = "high_similarity" if similar['similarity'] >= 0.9 else "league_context"
                    confidence = min(95, int(similar['similarity'] * 100))
                    
                    success, message = self.mapping_manager.create_mapping_suggestion(
                        similar['player_name'], 
                        official_name, 
                        mapping_type, 
                        confidence
                    )
                    
                    if success:
                        mappings_created += 1
                        print(f"      ✅ {message}")
                    else:
                        print(f"      ❌ {message}")
                else:
                    print(f"      📝 Would create mapping: '{similar['player_name']}' → '{official_name}'")
            
            print()
        
        print(f"📊 Summary:")
        print(f"   Similar names found: {mappings_found}")
        if dry_run:
            print(f"   Would create mappings: {mappings_found}")
        else:
            print(f"   Mappings created: {mappings_created}")
        
        return mappings_created if not dry_run else mappings_found
    
    def create_safe_mappings_1fb(self, dry_run=True, min_similarity=0.85):
        """Create mappings based on 1FB division context"""
        print(f"🔍 Analyzing official 1FB players for safe mappings...")
        print(f"   Minimum similarity: {min_similarity}")
        print(f"   Dry run: {dry_run}")
        print()
        
        mappings_created = 0
        mappings_found = 0
        
        for official_name in self.official_1fb_players:
            print(f"🔸 Analyzing: {official_name}")
            
            # Find which 1FB teams this player is associated with
            player_teams = self.find_team_for_official_player_1fb(official_name)
            
            if not player_teams:
                print(f"   ⚠️  No team associations found in database")
                continue
            
            print(f"   Teams: {', '.join(player_teams)}")
            
            # Find similar names in those teams
            similar_players = self.find_similar_names_in_teams(
                official_name, player_teams, min_similarity
            )
            
            if not similar_players:
                print(f"   ✅ No similar names found (already correct)")
                continue
            
            mappings_found += len(similar_players)
            
            for similar in similar_players:
                print(f"   🎯 Found similar: '{similar['player_name']}' (similarity: {similar['similarity']:.2f})")
                print(f"      Team: {similar['team_name']}")
                
                if not dry_run:
                    # Check if mapping already exists
                    existing_mappings = self.mapping_manager.list_suggestions('confirmed')
                    source_already_mapped = any(
                        m['source_name'] == similar['player_name'] 
                        for m in existing_mappings
                    )
                    
                    if source_already_mapped:
                        print(f"      ⏭️  Already mapped")
                        continue
                    
                    # Create mapping
                    mapping_type = "high_similarity" if similar['similarity'] >= 0.9 else "league_context"
                    confidence = min(95, int(similar['similarity'] * 100))
                    
                    success, message = self.mapping_manager.create_mapping_suggestion(
                        similar['player_name'], 
                        official_name, 
                        mapping_type, 
                        confidence
                    )
                    
                    if success:
                        mappings_created += 1
                        print(f"      ✅ {message}")
                    else:
                        print(f"      ❌ {message}")
                else:
                    print(f"      📝 Would create mapping: '{similar['player_name']}' → '{official_name}'")
            
            print()
        
        print(f"📊 Summary:")
        print(f"   Similar names found: {mappings_found}")
        if dry_run:
            print(f"   Would create mappings: {mappings_found}")
        else:
            print(f"   Mappings created: {mappings_created}")
        
        return mappings_created if not dry_run else mappings_found
    
    def find_team_for_official_player_1fb(self, official_name):
        """Try to determine which 1FB team an official player belongs to"""
        teams = self.get_player_teams(official_name)
        
        # Filter for 1FB teams
        matching_1fb_teams = []
        for team in teams:
            for div_team in self.div_1fb_teams:
                if div_team.lower() in team.lower():
                    matching_1fb_teams.append(team)
        
        return matching_1fb_teams

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 league_based_mapping.py <command> [args...]")
        print("")
        print("Commands:")
        print("  analyze [min_similarity]    - Analyze potential 3A mappings (default: 0.85)")
        print("  analyze-1fb [min_similarity] - Analyze potential 1FB mappings (default: 0.85)")
        print("  create [min_similarity]     - Create 3A mappings (default: 0.85)")
        print("  create-1fb [min_similarity] - Create 1FB mappings (default: 0.85)")
        print("  teams <player_name>         - Show teams for a player")
        print("")
        print("Examples:")
        print("  python3 league_based_mapping.py analyze 0.8")
        print("  python3 league_based_mapping.py analyze-1fb 0.8")
        print("  python3 league_based_mapping.py create-1fb 0.9")
        print("  python3 league_based_mapping.py teams 'Mats Andersson'")
        return 1
    
    mapper = LeagueBasedMapper()
    command = sys.argv[1]
    
    if command == "analyze":
        min_similarity = float(sys.argv[2]) if len(sys.argv) > 2 else 0.85
        mapper.create_safe_mappings(dry_run=True, min_similarity=min_similarity)
    
    elif command == "analyze-1fb":
        min_similarity = float(sys.argv[2]) if len(sys.argv) > 2 else 0.85
        mapper.create_safe_mappings_1fb(dry_run=True, min_similarity=min_similarity)
    
    elif command == "create":
        min_similarity = float(sys.argv[2]) if len(sys.argv) > 2 else 0.85
        mapper.create_safe_mappings(dry_run=False, min_similarity=min_similarity)
    
    elif command == "create-1fb":
        min_similarity = float(sys.argv[2]) if len(sys.argv) > 2 else 0.85
        mapper.create_safe_mappings_1fb(dry_run=False, min_similarity=min_similarity)
    
    elif command == "teams":
        if len(sys.argv) < 3:
            print("Usage: teams <player_name>")
            return 1
        player_name = sys.argv[2]
        teams = mapper.get_player_teams(player_name)
        print(f"Teams for '{player_name}':")
        for team in teams:
            print(f"  - {team}")
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())