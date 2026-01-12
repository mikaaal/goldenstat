#!/usr/bin/env python3
"""
Generate match URLs for all divisions found in current_match_urls directory
"""
import os
import re
from generate_match_urls import MatchUrlGenerator

def extract_division_ids():
    """Extract unique division IDs from existing files"""
    division_ids = set()

    if not os.path.exists('current_match_urls'):
        print("❌ current_match_urls directory not found")
        return []

    for filename in os.listdir('current_match_urls'):
        if filename.endswith('.txt') and not filename.endswith('_backup_2024host.txt'):
            # Extract pattern t_XXXX_YYYY from filename
            match = re.match(r'(t_[^_]+_\d+)_match_urls', filename)
            if match:
                division_ids.add(match.group(1))

    return sorted(list(division_ids))

def main():
    print("Generating match URLs for all divisions\n")

    # Extract division IDs from existing files
    division_ids = extract_division_ids()

    if not division_ids:
        print("ERROR: No division IDs found")
        return 1

    print(f"Found {len(division_ids)} divisions:")
    for div_id in division_ids:
        print(f"   - {div_id}")
    print()

    # Generate URLs for each division
    generator = MatchUrlGenerator()

    for i, tdid in enumerate(division_ids, 1):
        print(f"\n{'='*60}")
        print(f"Processing {i}/{len(division_ids)}: {tdid}")
        print('='*60)

        # Determine output filename based on existing file pattern
        existing_files = [f for f in os.listdir('current_match_urls')
                         if f.startswith(f"{tdid}_match_urls")]

        if existing_files:
            output_file = os.path.join('current_match_urls', existing_files[0])
            print(f"Updating existing file: {existing_files[0]}")
        else:
            output_file = os.path.join('current_match_urls', f"{tdid}_match_urls.txt")
            print(f"Creating new file: {tdid}_match_urls.txt")

        generator.save_urls_to_file(tdid, output_file)

    print(f"\n{'='*60}")
    print(f"Completed processing {len(division_ids)} divisions")
    print('='*60)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
