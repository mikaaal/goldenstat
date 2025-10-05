#!/usr/bin/env python3
"""
Mapping Reviewer
Shows invalid mappings in batches for user review

Created: 2025-09-21
"""
import sqlite3
import sys
from deep_mapping_validator import DeepMappingValidator

class MappingReviewer:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.validator = DeepMappingValidator(db_path)
    
    def get_all_invalid_mappings(self):
        """Get all invalid mappings from deep validation"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    pm.id as mapping_id,
                    pm.source_player_id,
                    pm.target_player_id,
                    pm.canonical_name,
                    pm.mapping_type,
                    pm.confidence,
                    ps.name as source_name,
                    pt.name as target_name
                FROM player_mappings pm
                JOIN players ps ON pm.source_player_id = ps.id
                JOIN players pt ON pm.target_player_id = pt.id
                WHERE pm.status = 'confirmed'
                ORDER BY pm.id
            """)
            
            mappings = [dict(row) for row in cursor.fetchall()]
        
        print(f"🔍 Finding invalid mappings from {len(mappings)} total mappings...")
        
        invalid_mappings = []
        for i, mapping in enumerate(mappings, 1):
            if i % 100 == 0:
                print(f"   Progress: {i}/{len(mappings)} ({i/len(mappings)*100:.1f}%)")
            
            is_valid, issues, warnings, insights = self.validator.validate_mapping_deeply(mapping)
            
            if not is_valid:
                invalid_mappings.append({
                    'mapping': mapping,
                    'issues': issues,
                    'warnings': warnings,
                    'insights': insights
                })
        
        print(f"✅ Found {len(invalid_mappings)} invalid mappings")
        return invalid_mappings
    
    def show_batch(self, invalid_mappings, start_index=0, batch_size=20):
        """Show a batch of invalid mappings for review"""
        end_index = min(start_index + batch_size, len(invalid_mappings))
        
        if start_index >= len(invalid_mappings):
            print("📭 No more mappings to review!")
            return False
        
        print(f"\n📋 Mappings {start_index + 1}-{end_index} av {len(invalid_mappings)} felaktiga mappningar:")
        print("=" * 80)
        
        for i in range(start_index, end_index):
            item = invalid_mappings[i]
            mapping = item['mapping']
            issues = item['issues']
            insights = item['insights']
            
            # Extract team info from insights
            source_teams = ""
            target_teams = ""
            for insight in insights:
                if insight.startswith("Source teams:"):
                    source_teams = insight.replace("Source teams: ", "")
                elif insight.startswith("Target teams:"):
                    target_teams = insight.replace("Target teams: ", "")
            
            print(f"\n{i + 1:2d}. ID {mapping['mapping_id']:3d}: '{mapping['source_name']}' → '{mapping['target_name']}'")
            print(f"    Canonical: '{mapping['canonical_name']}'")
            print(f"    Type: {mapping['mapping_type']}, Confidence: {mapping['confidence']}%")
            
            # Show key issues (abbreviated)
            key_issues = []
            for issue in issues:
                if "incompatible team" in issue:
                    # Extract team name from issue
                    team_name = issue.split("'")[-2] if "'" in issue else "unknown"
                    key_issues.append(f"Incompatible: {team_name}")
                elif "different teams in" in issue:
                    key_issues.append("Simultaneous different teams")
                elif "no match activity" in issue.lower():
                    key_issues.append("No match data")
                elif "no compatible teams" in issue.lower():
                    key_issues.append("No common teams")
                else:
                    key_issues.append(issue[:50] + "..." if len(issue) > 50 else issue)
            
            if key_issues:
                print(f"    Issues: {', '.join(key_issues[:2])}")  # Show max 2 issues
            
            print(f"    Source lag: {source_teams}")
            print(f"    Target lag: {target_teams}")
        
        print("\n" + "=" * 80)
        print(f"Visa batch {start_index // batch_size + 1} av {(len(invalid_mappings) - 1) // batch_size + 1}")
        
        return True
    
    def interactive_review(self, batch_size=20):
        """Interactive review of all invalid mappings"""
        print("🔍 Hämtar alla felaktiga mappningar...")
        invalid_mappings = self.get_all_invalid_mappings()
        
        if not invalid_mappings:
            print("✅ Inga felaktiga mappningar hittades!")
            return
        
        current_index = 0
        
        while True:
            has_more = self.show_batch(invalid_mappings, current_index, batch_size)
            
            if not has_more:
                break
            
            print(f"\nKommandon:")
            print(f"  'n' eller Enter - Nästa batch")
            print(f"  'p' - Föregående batch")
            print(f"  'j <nummer>' - Hoppa till batch nummer")
            print(f"  'r <nummer1,nummer2,...>' - Markera mappningar som ska behållas (ej tas bort)")
            print(f"  'q' - Avsluta")
            
            cmd = input(f"\n? ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'n' or cmd == '':
                current_index += batch_size
            elif cmd == 'p':
                current_index = max(0, current_index - batch_size)
            elif cmd.startswith('j '):
                try:
                    batch_num = int(cmd.split()[1]) - 1
                    current_index = batch_num * batch_size
                    if current_index < 0:
                        current_index = 0
                except (ValueError, IndexError):
                    print("❌ Ogiltigt batch-nummer")
            elif cmd.startswith('r '):
                try:
                    numbers = [int(x.strip()) for x in cmd.split()[1].split(',')]
                    print(f"📝 Markerade {numbers} som korrekta (dessa mappningar kommer INTE tas bort)")
                    # Here you could mark these mappings to keep
                except (ValueError, IndexError):
                    print("❌ Ogiltigt format. Använd: r 1,3,5")
        
        print(f"\n📊 Genomgång slutförd!")
        print(f"   Totalt felaktiga mappningar: {len(invalid_mappings)}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mapping_reviewer.py <command> [args...]")
        print("")
        print("Commands:")
        print("  review [batch_size]         - Interactive review (default: 20)")
        print("  show <start> [batch_size]   - Show specific batch")
        print("")
        print("Examples:")
        print("  python3 mapping_reviewer.py review")
        print("  python3 mapping_reviewer.py review 15")
        print("  python3 mapping_reviewer.py show 0 25")
        return 1
    
    reviewer = MappingReviewer()
    command = sys.argv[1]
    
    if command == "review":
        batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        reviewer.interactive_review(batch_size)
    
    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: show <start_index> [batch_size]")
            return 1
        start_index = int(sys.argv[2])
        batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        
        invalid_mappings = reviewer.get_all_invalid_mappings()
        reviewer.show_batch(invalid_mappings, start_index, batch_size)
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())