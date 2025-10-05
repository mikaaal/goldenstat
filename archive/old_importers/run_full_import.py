#!/usr/bin/env python3
"""
Run Full Import - Automatic Version
Runs the complete import for t_jM8s_0341 automatically
"""
from smart_full_import import SmartFullImporter

def main():
    print("=== RUNNING FULL IMPORT FOR t_jM8s_0341 ===")
    print("This will import all 110 matches with smart player matching")
    print("Database backup will be created automatically")

    importer = SmartFullImporter()

    try:
        # Run full import
        success = importer.run_full_import("t_jM8s_0341_match_urls.txt")

        if success:
            print("\n=== IMPORT COMPLETED SUCCESSFULLY ===")
            print(f"Backup available at: {importer.backup_path}")
            print("If you need to rollback, manually copy the backup file")
        else:
            print("\n=== IMPORT FAILED ===")
            print("Backup was automatically restored")

    except KeyboardInterrupt:
        print("\nImport interrupted by user")
        print("Restoring backup...")
        importer.restore_backup()

    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Restoring backup...")
        importer.restore_backup()

if __name__ == "__main__":
    main()