# Smart Import Handler Guide

## Overview

The Smart Import Handler (`smart_import_handler.py`) is designed to solve the player name disambiguation problem that occurs during weekly data imports. After our database cleanup where players were separated by club (e.g., "Mats Andersson" became "Mats Andersson (Dartanjang)", "Mats Andersson (SSDC)", etc.), incoming import data needs to be intelligently routed to the correct player variants.

## Key Problems Solved

### 1. Club-Separated Players
- **Problem**: Import data contains "Mats Andersson" but database now has multiple variants
- **Solution**: Uses team context to match to correct variant like "Mats Andersson (SSDC)"

### 2. Case Variations
- **Problem**: Import contains "mats andersson" but database has "Mats Andersson"
- **Solution**: Case-insensitive matching with existing mappings prioritized

### 3. Club Name Standardization
- **Problem**: Import has "AIK Dart" but database has "AIK Dartförening"
- **Solution**: Standardization rules map variants to canonical names

### 4. Hyphen/Space Variations
- **Problem**: Import has "Lars Erik Renström" but database has "Lars-Erik Renström"
- **Solution**: Automatic detection and mapping of hyphen/space variants

## How It Works

### SmartPlayerMatcher Class

```python
from smart_import_handler import SmartPlayerMatcher

matcher = SmartPlayerMatcher("goldenstat.db")
result = matcher.find_player_match("Mats Andersson", "SSDC SL6")
```

### Return Format

Every match attempt returns a dictionary with:
- `action`: Type of match found (see Action Types below)
- `player_id`: Database ID of matched player (or None)
- `player_name`: Canonical name to use
- `confidence`: Match confidence (0-100)
- `notes`: Human-readable explanation

### Action Types

| Action | Description | Confidence |
|--------|-------------|------------|
| `exact_match` | Perfect name match found | 100 |
| `club_specific` | Matched to club-separated variant | 95 |
| `club_specific_standardized` | Matched via club name standardization | 93 |
| `existing_mapping` | Used pre-existing mapping from database | 90 |
| `case_variation` | Single case variation found | 85 |
| `case_variation_prioritized` | Multiple case matches, selected best | 88 |
| `hyphen_space_variation` | Hyphen/space variant found | 80 |
| `create_club_variant` | Need to create new club variant | 90 |
| `create_new` | Completely new player | 0 |

## Integration Example

```python
def process_import_match(player_name, team_name, sub_match_id):
    """Process a single player from import data"""
    matcher = SmartPlayerMatcher()
    result = matcher.find_player_match(player_name, team_name)

    if result['action'] == 'exact_match':
        # Use existing player directly
        return result['player_id']

    elif result['action'].startswith('club_specific'):
        # Found correct club variant
        return result['player_id']

    elif result['action'] == 'existing_mapping':
        # Use mapped player and create new mapping for this sub-match
        matcher.create_mapping_if_needed(
            sub_match_id,
            find_original_player_id(player_name),
            result['player_id'],
            result['player_name'],
            f"Import handler: {result['notes']}"
        )
        return result['player_id']

    elif result['action'] == 'create_club_variant':
        # Create new club-specific player
        new_player_id = create_new_player(result['player_name'])
        return new_player_id

    elif result['action'] == 'create_new':
        # Completely new player
        new_player_id = create_new_player(player_name)
        return new_player_id

    else:
        # Handle case variations and other mappings
        original_player_id = find_original_player_id(player_name)
        if original_player_id:
            matcher.create_mapping_if_needed(
                sub_match_id,
                original_player_id,
                result['player_id'],
                result['player_name'],
                f"Import handler: {result['notes']}"
            )
        return result['player_id']
```

## Current Database State

After our cleanup process, the handler is pre-loaded with:

### Separated Players (36 base names)
Key examples:
- **Mats Andersson**: 3 variants (SSDC, Dartanjang, AIK Dart)
- **Robert Goth**: 2 variants (AIK Dartförening, Mitt i DC)
- **Erik**: Multiple club variants
- **Magnus**: Multiple club variants

### Existing Mappings (437 total)
Examples:
- `marcus gavander` → `Marcus Gavander`
- `johan` → `Johan (Tyresö)`
- `erik` → `erik (Oilers)`

### Club Standardizations
- `AIK` / `AIK Dartförening` → `AIK Dart`
- `Engelen` → `HMT Dart`
- `Spikkastarna B` → `SpikKastarna`

## Testing Results

The handler was tested with realistic scenarios:

```
✅ 'Mats Andersson' + 'Dartanjang (2FB)' → Mats Andersson (Dartanjang)
✅ 'mats andersson' + 'SSDC SL6' → Mats Andersson (SSDC)
✅ 'marcus gavander' + 'Dartanjang' → Marcus Gavander (via mapping)
✅ 'Robert Goth' + 'AIK Dart' → Robert Goth (AIK Dartförening) (via standardization)
✅ 'Lars Erik Renström' → Lars Erik Renström (exact match)
✅ 'Lars-Erik Renström' → Lars-Erik Renström (exact match)
✅ 'TOMMY LINDSTRÖM' → create_new (correctly identified as new player)
```

## Weekly Import Integration

### Step 1: Pre-processing
```python
# Standardize team names before matching
team_name = matcher.standardize_club_name(raw_team_name)
player_name = matcher.normalize_player_name(raw_player_name)
```

### Step 2: Player Matching
```python
result = matcher.find_player_match(player_name, team_name)
```

### Step 3: Action Handling
Use the action type and confidence score to determine how to handle the match.

### Step 4: Mapping Creation
For non-exact matches, create mappings to ensure future consistency.

## Confidence Thresholds

Recommended handling by confidence level:
- **90-100**: Auto-accept, high confidence matches
- **80-89**: Auto-accept with logging for review
- **70-79**: Require manual verification
- **<70**: Require manual review

## Error Handling

The handler gracefully handles:
- Missing database connections
- Invalid player IDs
- Unicode normalization issues
- Missing team context
- Database constraint violations

## Maintenance

### Adding New Standardizations
Update the `standardize_club_name` method:

```python
standardizations = {
    'AIK': 'AIK Dart',
    'New Club Variant': 'Standard Club Name',
    # ... existing mappings
}
```

### Monitoring Mappings
Regularly check mapping creation:

```sql
SELECT mapping_reason, COUNT(*)
FROM sub_match_player_mappings
WHERE mapping_reason LIKE 'Import handler%'
GROUP BY mapping_reason;
```

## Performance

- **Pre-loading**: All mappings and separations loaded at startup
- **Caching**: Standardizations cached per instance
- **Database hits**: Minimized through pre-loaded data structures
- **Memory usage**: ~500KB for current dataset

The Smart Import Handler provides robust, automated handling of the complex player disambiguation challenges that arise from our multi-club database cleanup, ensuring weekly imports maintain data integrity while minimizing manual intervention.