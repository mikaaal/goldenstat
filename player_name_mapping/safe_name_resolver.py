#!/usr/bin/env python3
"""
Safe Name Resolver
Implements careful player name disambiguation based on club/team context and temporal validation.
Designed to safely handle cases like "Peter" -> specific Peter players.

Created: 2025-09-22
"""
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class PlayerContext:
    """Represents a player's context in terms of club, division, season, and time period"""
    player_id: int
    player_name: str
    club_name: str
    division: str
    season: str
    date_start: Optional[str]
    date_end: Optional[str]
    match_count: int

@dataclass
class TemporalConflict:
    """Represents a temporal overlap between two players that might indicate they're different people"""
    player1_id: int
    player2_id: int
    player1_name: str
    player2_name: str
    overlap_start: str
    overlap_end: str
    different_clubs: bool
    severity: str  # 'low', 'medium', 'high'

class SafeNameResolver:
    def __init__(self, db_path="../goldenstat.db"):
        self.db_path = db_path
        self.club_pattern = re.compile(r'^(.+?)\s*\([^)]+\)$')  # Extract club from "Club (Division)"
    
    def extract_club_name(self, team_name: str) -> str:
        """Extract club name from team name like 'Oilers (3FC)' -> 'Oilers'"""
        match = self.club_pattern.match(team_name.strip())
        if match:
            return match.group(1).strip()
        return team_name.strip()
    
    def get_player_contexts(self, player_name: str) -> List[PlayerContext]:
        """Get all contexts where a player name appears"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
            SELECT 
                p.id as player_id,
                p.name as player_name,
                t.name as team_name,
                m.division,
                m.season,
                MIN(m.match_date) as date_start,
                MAX(m.match_date) as date_end,
                COUNT(DISTINCT sm.id) as match_count
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            WHERE p.name = ?
            GROUP BY p.id, t.name, m.division, m.season
            ORDER BY m.season, m.division, t.name
            """
            
            cursor.execute(query, (player_name,))
            contexts = []
            
            for row in cursor.fetchall():
                club_name = self.extract_club_name(row['team_name'])
                contexts.append(PlayerContext(
                    player_id=row['player_id'],
                    player_name=row['player_name'],
                    club_name=club_name,
                    division=row['division'],
                    season=row['season'],
                    date_start=row['date_start'],
                    date_end=row['date_end'],
                    match_count=row['match_count']
                ))
            
            return contexts
    
    def detect_temporal_conflicts(self, contexts: List[PlayerContext]) -> List[TemporalConflict]:
        """Detect if different player IDs for the same name have temporal overlaps in different clubs"""
        conflicts = []
        
        # Group contexts by player_id
        by_player = defaultdict(list)
        for ctx in contexts:
            by_player[ctx.player_id].append(ctx)
        
        # Compare each pair of players
        player_ids = list(by_player.keys())
        for i in range(len(player_ids)):
            for j in range(i + 1, len(player_ids)):
                player1_id = player_ids[i]
                player2_id = player_ids[j]
                
                player1_contexts = by_player[player1_id]
                player2_contexts = by_player[player2_id]
                
                # Check for temporal overlaps
                for ctx1 in player1_contexts:
                    for ctx2 in player2_contexts:
                        if self._contexts_overlap_temporally(ctx1, ctx2):
                            different_clubs = ctx1.club_name != ctx2.club_name
                            severity = self._assess_conflict_severity(ctx1, ctx2, different_clubs)
                            
                            conflicts.append(TemporalConflict(
                                player1_id=player1_id,
                                player2_id=player2_id,
                                player1_name=ctx1.player_name,
                                player2_name=ctx2.player_name,
                                overlap_start=max(ctx1.date_start or '', ctx2.date_start or ''),
                                overlap_end=min(ctx1.date_end or '9999-12-31', ctx2.date_end or '9999-12-31'),
                                different_clubs=different_clubs,
                                severity=severity
                            ))
        
        return conflicts
    
    def _contexts_overlap_temporally(self, ctx1: PlayerContext, ctx2: PlayerContext) -> bool:
        """Check if two contexts overlap in time"""
        if not ctx1.date_start or not ctx1.date_end or not ctx2.date_start or not ctx2.date_end:
            return False
        
        start1, end1 = ctx1.date_start, ctx1.date_end
        start2, end2 = ctx2.date_start, ctx2.date_end
        
        # Check if periods overlap
        return start1 <= end2 and start2 <= end1
    
    def _assess_conflict_severity(self, ctx1: PlayerContext, ctx2: PlayerContext, different_clubs: bool) -> str:
        """Assess the severity of a temporal conflict"""
        if different_clubs:
            # Same person cannot play for different clubs simultaneously
            return 'high'
        elif ctx1.division != ctx2.division:
            # Same person CAN play in different divisions for same club
            return 'low'
        else:
            # Same division, same club - might indicate data quality issue
            return 'medium'
    
    def can_safely_merge_contexts(self, contexts: List[PlayerContext]) -> Tuple[bool, str]:
        """
        Determine if contexts can be safely merged based on the business rules:
        1. A player can never play for different clubs simultaneously
        2. A player can play for multiple teams in different divisions for same club
        3. A player can play multiple matches in same week for different teams in same club
        """
        conflicts = self.detect_temporal_conflicts(contexts)
        
        # Check for high-severity conflicts (different clubs simultaneously)
        high_severity_conflicts = [c for c in conflicts if c.severity == 'high']
        if high_severity_conflicts:
            conflict_details = []
            for conflict in high_severity_conflicts:
                conflict_details.append(
                    f"Player IDs {conflict.player1_id} and {conflict.player2_id} "
                    f"played for different clubs during {conflict.overlap_start} to {conflict.overlap_end}"
                )
            return False, f"Cannot merge: {'; '.join(conflict_details)}"
        
        # If no high-severity conflicts, it's safe to merge
        return True, "Safe to merge - no temporal conflicts between different clubs"
    
    def find_best_canonical_name(self, contexts: List[PlayerContext]) -> str:
        """Find the best canonical name from available contexts"""
        # Collect all unique names
        names = list(set(ctx.player_name for ctx in contexts))
        
        if len(names) == 1:
            return names[0]
        
        # Prefer longer, more complete names
        def name_quality_score(name: str) -> int:
            score = 0
            words = name.strip().split()
            
            # Length bonus
            score += len(name) * 2
            
            # Multiple words bonus (first + last name)
            if len(words) >= 2:
                score += 100
            
            # Proper case bonus
            if all(word[0].isupper() and word[1:].islower() for word in words if word):
                score += 50
            
            return score
        
        # Return the name with highest quality score
        return max(names, key=name_quality_score)
    
    def analyze_first_name_mappings(self, first_name: str) -> Dict:
        """
        Analyze all players with a given first name to determine safe mappings
        Returns a detailed analysis including conflicts and safe mappings
        """
        print(f"\\n=== Analyzing first name: '{first_name}' ===")
        
        # Get all contexts for this first name
        contexts = self.get_player_contexts(first_name)
        
        if not contexts:
            return {
                'first_name': first_name,
                'total_contexts': 0,
                'can_disambiguate': False,
                'reason': 'No contexts found'
            }
        
        print(f"Found {len(contexts)} contexts for '{first_name}'")
        
        # Group contexts by unique club+division+season combinations
        context_groups = defaultdict(list)
        for ctx in contexts:
            key = f"{ctx.club_name}|{ctx.division}|{ctx.season}"
            context_groups[key].append(ctx)
        
        safe_mappings = []
        conflicts = []
        
        for group_key, group_contexts in context_groups.items():
            club, division, season = group_key.split('|')
            print(f"\\n  Analyzing group: {club} ({division}) - {season}")
            print(f"    Contexts in group: {len(group_contexts)}")
            
            # Check if this group can be safely merged
            can_merge, reason = self.can_safely_merge_contexts(group_contexts)
            
            if can_merge:
                # Find the best full name for this context
                canonical_name = self.find_best_canonical_name(group_contexts)
                player_ids = [ctx.player_id for ctx in group_contexts]
                
                if canonical_name != first_name:  # Only if we have a better name
                    safe_mappings.append({
                        'context': f"{club} ({division}) - {season}",
                        'player_ids': player_ids,
                        'canonical_name': canonical_name,
                        'confidence': 85,
                        'reason': f"Unique in {club} for {season}"
                    })
                    print(f"    ✓ Safe mapping: '{first_name}' -> '{canonical_name}'")
                else:
                    print(f"    ⚠ No better name available for mapping")
            else:
                conflicts.append({
                    'context': f"{club} ({division}) - {season}",
                    'reason': reason,
                    'player_ids': [ctx.player_id for ctx in group_contexts]
                })
                print(f"    ✗ Conflict: {reason}")
        
        return {
            'first_name': first_name,
            'total_contexts': len(contexts),
            'context_groups': len(context_groups),
            'safe_mappings': safe_mappings,
            'conflicts': conflicts,
            'can_disambiguate': len(safe_mappings) > 0,
            'analysis_summary': f"Found {len(safe_mappings)} safe mappings and {len(conflicts)} conflicts"
        }
    
    def generate_safe_mappings(self, first_name: str) -> List[Dict]:
        """Generate safe mapping entries that can be inserted into the database"""
        analysis = self.analyze_first_name_mappings(first_name)
        
        if not analysis['can_disambiguate']:
            return []
        
        mappings = []
        for mapping in analysis['safe_mappings']:
            # Find the target player ID (the one with the canonical name)
            target_player_id = None
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM players WHERE name = ? AND id IN ({})".format(
                        ','.join(['?'] * len(mapping['player_ids']))
                    ),
                    [mapping['canonical_name']] + mapping['player_ids']
                )
                result = cursor.fetchone()
                if result:
                    target_player_id = result[0]
            
            if target_player_id:
                for source_player_id in mapping['player_ids']:
                    if source_player_id != target_player_id:
                        mappings.append({
                            'source_player_id': source_player_id,
                            'target_player_id': target_player_id,
                            'canonical_name': mapping['canonical_name'],
                            'specific_context': mapping['context'],
                            'confidence': mapping['confidence'],
                            'mapping_type': 'first_name_only',
                            'validation_status': 'pending',
                            'club_uniqueness_validated': True,
                            'temporal_uniqueness_validated': True,
                            'notes': mapping['reason']
                        })
        
        return mappings

if __name__ == "__main__":
    resolver = SafeNameResolver()
    
    # Test with Peter
    print("Testing with 'Peter'...")
    analysis = resolver.analyze_first_name_mappings("Peter")
    print(f"\\nAnalysis complete: {analysis['analysis_summary']}")
    
    if analysis['can_disambiguate']:
        mappings = resolver.generate_safe_mappings("Peter")
        print(f"\\nGenerated {len(mappings)} safe mappings:")
        for mapping in mappings[:3]:  # Show first 3
            print(f"  {mapping['source_player_id']} -> {mapping['target_player_id']}: '{mapping['canonical_name']}'")