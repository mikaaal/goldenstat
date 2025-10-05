#!/usr/bin/env python3
"""
Import specific season from n01darts.com
"""
import sys
from new_format_importer import NewFormatImporter

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 import_season.py <season_url>")
        print("Example: python3 import_season.py 'https://n01darts.com/n01/league/season.php?id=t_jM8s_0341'")
        return 1
    
    season_url = sys.argv[1]
    print(f"🎯 Starting import of season from: {season_url}")
    
    try:
        importer = NewFormatImporter()
        
        # The NewFormatImporter might need different methods
        # Let me check what methods are available
        print("Available methods:")
        methods = [method for method in dir(importer) if not method.startswith('_')]
        for method in methods:
            print(f"  - {method}")
        
        # Try to find a method that can import from URL
        if hasattr(importer, 'process_match_from_url'):
            print("📥 Using process_match_from_url method...")
            result = importer.process_match_from_url(season_url)
            print(f"✅ Import completed: {result}")
        else:
            print("❌ No suitable import method found")
            return 1
            
    except Exception as e:
        print(f"❌ Error during import: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())