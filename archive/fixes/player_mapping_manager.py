#!/usr/bin/env python3
"""
Player Mapping Manager
Handles creation, management, and application of player name mappings

Created: 2025-09-19
"""
import sqlite3
import sys
import json
from datetime import datetime
from find_duplicate_players import DuplicatePlayerFinder

class PlayerMappingManager:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.duplicate_finder = DuplicatePlayerFinder(db_path)
    
    def get_player_id(self, player_name):
        """Get player ID by name"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def choose_canonical_name(self, name1, name2):
        """Choose which name should be the canonical one based on quality heuristics"""
        # Rules for choosing the better name:
        # 1. Proper title case is ALWAYS preferred (First Last)
        # 2. Longer name is usually better (more complete)
        # 3. Names with both first and last name are better than single names
        
        def normalize_to_title_case(name):
            """Convert name to proper title case"""
            words = name.strip().split()
            return ' '.join(word.capitalize() for word in words if word)
        
        def score_name(name):
            score = 0
            words = name.strip().split()
            
            # Length bonus (longer = more complete)
            score += len(name) * 2
            
            # Multiple words bonus (first + last name)
            if len(words) >= 2:
                score += 100
            
            # Title case bonus (each word starts with capital)
            title_case_words = sum(1 for word in words if word and word[0].isupper() and word[1:].islower())
            if title_case_words == len(words) and len(words) > 0:
                score += 200  # VERY HIGH bonus for perfect title case
            
            # First letter capital bonus
            if name and name[0].isupper():
                score += 20
            
            # All lowercase penalty
            if name.islower():
                score -= 50
            
            # ALL CAPS penalty  
            if name.isupper():
                score -= 40
            
            return score
        
        # Always normalize both names to title case first
        normalized_name1 = normalize_to_title_case(name1)
        normalized_name2 = normalize_to_title_case(name2)
        
        # If both normalize to the same thing, prefer the one that was already in title case
        if normalized_name1 == normalized_name2:
            score1 = score_name(name1)
            score2 = score_name(name2)
            
            if score1 >= score2:
                return normalized_name1, name2  # Use normalized as canonical, original as source
            else:
                return normalized_name2, name1
        
        # Otherwise, score the normalized versions and pick the better structure
        score1 = score_name(normalized_name1)
        score2 = score_name(normalized_name2)
        
        if score1 >= score2:
            return normalized_name1, name2  # canonical, source
        else:
            return normalized_name2, name1  # canonical, source
    
    def create_mapping_suggestion(self, source_player_name, target_player_name, mapping_type, confidence=80):
        """Create a mapping suggestion in the database"""
        source_id = self.get_player_id(source_player_name)
        target_id = self.get_player_id(target_player_name)
        
        if not source_id or not target_id:
            return False, f"Player not found: {source_player_name if not source_id else target_player_name}"
        
        # Choose canonical name
        canonical_name, _ = self.choose_canonical_name(source_player_name, target_player_name)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if mapping already exists
            cursor.execute("SELECT id FROM player_mappings WHERE source_player_id = ?", (source_id,))
            if cursor.fetchone():
                return False, f"Mapping already exists for {source_player_name}"
            
            # Insert mapping suggestion
            cursor.execute("""
                INSERT INTO player_mappings 
                (source_player_id, target_player_id, canonical_name, confidence, mapping_type, status)
                VALUES (?, ?, ?, ?, ?, 'suggested')
            """, (source_id, target_id, canonical_name, confidence, mapping_type))
            
            conn.commit()
            return True, f"Created mapping: {source_player_name} -> {canonical_name}"
    
    def generate_suggestions_from_duplicates(self, team_pattern=None, min_confidence=70):
        """Generate mapping suggestions from duplicate detection"""
        print(f"🔍 Generating mapping suggestions...")
        if team_pattern:
            print(f"   Team pattern: {team_pattern}")
        print(f"   Minimum confidence: {min_confidence}")
        
        # Get duplicates
        teams_data = self.duplicate_finder.get_players_by_team(team_pattern)
        suggestions_created = 0
        suggestions_skipped = 0
        
        for team_name, players in teams_data.items():
            duplicates = self.duplicate_finder.find_duplicates_in_team(team_name, players)
            
            for dup in duplicates:
                # Convert similarity to confidence (0.85+ = 90, etc.)
                confidence = min(95, int(dup['similarity'] * 100))
                
                if confidence < min_confidence:
                    continue
                
                p1_name = dup['player1']['player_name']
                p2_name = dup['player2']['player_name']
                mapping_type = dup['match_type']
                
                # Choose which should be source and which should be target
                canonical_name, source_name = self.choose_canonical_name(p1_name, p2_name)
                target_name = canonical_name
                
                success, message = self.create_mapping_suggestion(
                    source_name, target_name, mapping_type, confidence
                )
                
                if success:
                    suggestions_created += 1
                    print(f"   ✅ {message}")
                else:
                    suggestions_skipped += 1
                    if "already exists" not in message:
                        print(f"   ⚠️  {message}")
        
        print(f"\n📊 Suggestions generated:")
        print(f"   Created: {suggestions_created}")
        print(f"   Skipped: {suggestions_skipped}")
        
        return suggestions_created
    
    def list_suggestions(self, status='suggested', limit=None):
        """List mapping suggestions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    pm.*,
                    ps.name as source_name,
                    pt.name as target_name
                FROM player_mappings pm
                JOIN players ps ON pm.source_player_id = ps.id
                JOIN players pt ON pm.target_player_id = pt.id
                WHERE pm.status = ?
                ORDER BY pm.confidence DESC, pm.created_at DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (status,))
            return [dict(row) for row in cursor.fetchall()]
    
    def approve_mapping(self, mapping_id, approved_by="admin"):
        """Approve a mapping suggestion"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE player_mappings 
                SET status = 'confirmed', 
                    approved_by = ?, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (approved_by, mapping_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True, "Mapping approved"
            else:
                return False, "Mapping not found"
    
    def reject_mapping(self, mapping_id, notes=None):
        """Reject a mapping suggestion"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE player_mappings 
                SET status = 'rejected', 
                    notes = ?, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (notes, mapping_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True, "Mapping rejected"
            else:
                return False, "Mapping not found"
    
    def show_mapping_review_interface(self, limit=10):
        """Show an interactive interface for reviewing mappings"""
        suggestions = self.list_suggestions('suggested', limit)
        
        if not suggestions:
            print("📭 No mapping suggestions to review!")
            return
        
        print(f"📋 {len(suggestions)} mapping suggestions to review:")
        print()
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"🔸 Suggestion {i}/{len(suggestions)} (ID: {suggestion['id']})")
            print(f"   Source: '{suggestion['source_name']}'")
            print(f"   Target: '{suggestion['target_name']}'")
            print(f"   Canonical: '{suggestion['canonical_name']}'")
            print(f"   Type: {suggestion['mapping_type']}")
            print(f"   Confidence: {suggestion['confidence']}%")
            print(f"   Created: {suggestion['created_at']}")
            print()
    
    def export_mappings(self, output_file, status=None):
        """Export mappings to JSON file"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            where_clause = ""
            params = []
            if status:
                where_clause = "WHERE pm.status = ?"
                params = [status]
            
            cursor.execute(f"""
                SELECT 
                    pm.*,
                    ps.name as source_name,
                    pt.name as target_name
                FROM player_mappings pm
                JOIN players ps ON pm.source_player_id = ps.id
                JOIN players pt ON pm.target_player_id = pt.id
                {where_clause}
                ORDER BY pm.id
            """, params)
            
            mappings = [dict(row) for row in cursor.fetchall()]
            
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'total_mappings': len(mappings),
                'status_filter': status,
                'mappings': mappings
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Exported {len(mappings)} mappings to {output_file}")
    
    def approve_all_suggested(self, min_confidence=80, dry_run=False):
        """Approve all suggested mappings above a certain confidence threshold"""
        suggested = self.list_suggestions('suggested')
        
        if not suggested:
            print("📭 No suggested mappings found!")
            return 0
        
        # Filter by confidence
        eligible = [s for s in suggested if s['confidence'] >= min_confidence]
        
        print(f"📋 Found {len(suggested)} suggested mappings")
        print(f"🎯 {len(eligible)} mappings above {min_confidence}% confidence threshold")
        
        if dry_run:
            print("\n🔍 DRY RUN - Would approve these mappings:")
            for s in eligible:
                print(f"   {s['id']}: {s['source_name']} -> {s['canonical_name']} ({s['confidence']}%)")
            return len(eligible)
        
        if not eligible:
            print("❌ No mappings meet the confidence threshold")
            return 0
        
        print(f"\n📝 Approving {len(eligible)} mappings...")
        approved_count = 0
        
        for s in eligible:
            success, message = self.approve_mapping(s['id'], "bulk_approval")
            if success:
                approved_count += 1
                print(f"   ✅ {s['source_name']} -> {s['canonical_name']} ({s['confidence']}%)")
            else:
                print(f"   ❌ Failed: {s['source_name']} -> {s['canonical_name']} - {message}")
        
        print(f"\n🎉 Successfully approved {approved_count}/{len(eligible)} mappings")
        return approved_count

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 player_mapping_manager.py <command> [args...]")
        print("")
        print("Commands:")
        print("  generate <team_pattern> [min_confidence] - Generate mapping suggestions for team (default: 70%)")
        print("  list [status]               - List mapping suggestions (default: suggested)")
        print("  review [limit]              - Show review interface (default: 10)")
        print("  approve <mapping_id>        - Approve a mapping")
        print("  approve-all [min_confidence] [--dry-run] - Approve all suggested mappings (default: 80%)")
        print("  reject <mapping_id> [notes] - Reject a mapping")
        print("  export <file> [status]      - Export mappings to JSON")
        print("")
        print("Examples:")
        print("  python3 player_mapping_manager.py generate Dartanjang")
        print("  python3 player_mapping_manager.py generate Dartanjang 50")
        print("  python3 player_mapping_manager.py review 5")
        print("  python3 player_mapping_manager.py approve 1")
        print("  python3 player_mapping_manager.py approve-all 90 --dry-run")
        print("  python3 player_mapping_manager.py approve-all 80")
        print("  python3 player_mapping_manager.py export mappings.json confirmed")
        return 1
    
    manager = PlayerMappingManager()
    command = sys.argv[1]
    
    if command == "generate":
        if len(sys.argv) < 3:
            print("Usage: generate <team_pattern> [min_confidence]")
            return 1
        team_pattern = sys.argv[2]
        min_confidence = int(sys.argv[3]) if len(sys.argv) > 3 else 70
        
        print(f"🔍 Generating mapping suggestions...")
        print(f"   Team pattern: {team_pattern}")
        print(f"   Minimum confidence: {min_confidence}%")
        if min_confidence < 70:
            print(f"   ⚠️  Using low confidence threshold (reduced from default 70%)")
        print()
        
        suggestions_created = manager.generate_suggestions_from_duplicates(team_pattern, min_confidence)
        
        # Show new suggestions for review if any were created
        if suggestions_created > 0:
            print(f"\n📋 New suggestions to review:")
            suggestions = manager.list_suggestions('suggested', 20)
            
            # Show suggestions created with this run (filter by confidence if low threshold was used)
            if min_confidence < 70:
                low_conf_suggestions = [s for s in suggestions if s['confidence'] < 70]
                print(f"   Low-confidence suggestions (< 70%):")
                for i, s in enumerate(low_conf_suggestions, 1):
                    print(f"      {i}. {s['source_name']} -> {s['canonical_name']}")
                    print(f"         Confidence: {s['confidence']}%, Type: {s['mapping_type']}")
            
            print(f"\n💡 Use 'python3 player_mapping_manager.py review' to review all suggestions")
            print(f"💡 Use 'python3 player_mapping_manager.py approve-all {min_confidence}' to bulk approve")
    
    elif command == "list":
        status = sys.argv[2] if len(sys.argv) > 2 else 'suggested'
        suggestions = manager.list_suggestions(status)
        print(f"📋 {len(suggestions)} mappings with status '{status}':")
        for s in suggestions:
            print(f"   {s['id']}: {s['source_name']} -> {s['canonical_name']} ({s['confidence']}%)")
    
    elif command == "review":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        manager.show_mapping_review_interface(limit)
    
    elif command == "approve":
        if len(sys.argv) < 3:
            print("Usage: approve <mapping_id>")
            return 1
        mapping_id = int(sys.argv[2])
        success, message = manager.approve_mapping(mapping_id)
        print(f"{'✅' if success else '❌'} {message}")
    
    elif command == "approve-all":
        # Parse arguments
        min_confidence = 80  # default
        dry_run = False
        
        for i in range(2, len(sys.argv)):
            arg = sys.argv[i]
            if arg == "--dry-run":
                dry_run = True
            elif arg.isdigit():
                min_confidence = int(arg)
        
        approved_count = manager.approve_all_suggested(min_confidence, dry_run)
        if dry_run:
            print(f"\n🔍 Dry run complete. Would approve {approved_count} mappings.")
        else:
            print(f"\n✅ Bulk approval complete. Approved {approved_count} mappings.")
    
    elif command == "reject":
        if len(sys.argv) < 3:
            print("Usage: reject <mapping_id> [notes]")
            return 1
        mapping_id = int(sys.argv[2])
        notes = sys.argv[3] if len(sys.argv) > 3 else None
        success, message = manager.reject_mapping(mapping_id, notes)
        print(f"{'✅' if success else '❌'} {message}")
    
    elif command == "export":
        if len(sys.argv) < 3:
            print("Usage: export <file> [status]")
            return 1
        output_file = sys.argv[2]
        status = sys.argv[3] if len(sys.argv) > 3 else None
        manager.export_mappings(output_file, status)
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())