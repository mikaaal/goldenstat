#!/usr/bin/env python3
"""
Debug target player lookup for first name mapping
"""
import sqlite3

def debug_first_name_targets():
    """Debug vad som händer när vi söker target-spelarna"""
    print("=== DEBUG FIRST NAME TARGET LOOKUP ===")

    # Test cases från våra tester
    targets_to_check = [
        "Johan (Rockhangers)",
        "Johan Widholm",
        "Anders (VH Sportbar)",
        "Mats lundroth",
        "Mikael (Väsby)"
    ]

    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()

        for target_name in targets_to_check:
            print(f"\nSöker: '{target_name}'")

            # Exakt sökning
            cursor.execute("SELECT id, name FROM players WHERE name = ?", (target_name,))
            exact_result = cursor.fetchone()

            if exact_result:
                print(f"  [OK] Hittad: ID {exact_result[0]} - {exact_result[1]}")
            else:
                print(f"  [NOT FOUND] Inte hittad exakt")

                # Sök case-insensitive
                cursor.execute("SELECT id, name FROM players WHERE LOWER(name) = LOWER(?)", (target_name,))
                case_result = cursor.fetchone()

                if case_result:
                    print(f"  [CASE] Case-insensitive: ID {case_result[0]} - {case_result[1]}")
                else:
                    print(f"  [NOT FOUND] Inte hittad alls")

                    # Sök partiell matchning
                    cursor.execute("SELECT id, name FROM players WHERE name LIKE ?", (f"%{target_name}%",))
                    partial_results = cursor.fetchall()

                    if partial_results:
                        print(f"  [PARTIAL] Partiell matchning:")
                        for result in partial_results[:3]:  # Visa bara första 3
                            print(f"    ID {result[0]} - {result[1]}")
                    else:
                        print(f"  [NO MATCH] Ingen matchning alls")

if __name__ == "__main__":
    debug_first_name_targets()