-- Fix Mats Andersson mapping issue
-- ID 2319 was created as bare "Mats Andersson" instead of "Mats Andersson (AIK Dart)"
-- This caused find_player_match() to return exact_match on 2319 for ALL "Mats Andersson"
-- imports, bypassing the club-specific matching logic entirely.
-- Result: SSDC and Dartanjang matches incorrectly landed on 2319.

-- Step 1: Rename player 2319 to include club suffix
UPDATE players SET name = 'Mats Andersson (AIK Dart)' WHERE id = 2319;

-- Step 2: Update correct_player_name in all mappings pointing to 2319
UPDATE sub_match_player_mappings
SET correct_player_name = 'Mats Andersson (AIK Dart)'
WHERE correct_player_id = 2319;

-- Step 3: Move misrouted SSDC direct participations from 2319 to 2317
UPDATE sub_match_participants
SET player_id = 2317
WHERE player_id = 2319
AND sub_match_id IN (26774, 26776, 28184, 28185);

-- Step 4: Move misrouted Dartanjang direct participations from 2319 to 2318
UPDATE sub_match_participants
SET player_id = 2318
WHERE player_id = 2319
AND sub_match_id IN (26879, 26881, 27562, 27564);

-- Step 5: Move misrouted Dartanjang direct participations from 185 to 2318
UPDATE sub_match_participants
SET player_id = 2318
WHERE player_id = 185
AND sub_match_id IN (2457, 2458, 2656, 2657);

-- Step 6: Fix 4 Dartanjang mappings from 185->2319 to 185->2318
UPDATE sub_match_player_mappings
SET correct_player_id = 2318,
    correct_player_name = 'Mats Andersson (Dartanjang)',
    notes = 'Fixed: was incorrectly mapped to generic Mats Andersson'
WHERE id IN (12821, 12822, 12823, 12824);

-- Step 7: Fix 4 orphaned mappings from 397->2319 to 397->2318
UPDATE sub_match_player_mappings
SET correct_player_id = 2318,
    correct_player_name = 'Mats Andersson (Dartanjang)',
    notes = 'Fixed: was incorrectly mapped to generic Mats Andersson'
WHERE id IN (6306, 6307, 6308, 6309);
