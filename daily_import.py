#!/usr/bin/env python3
"""
🤖 AUTOMATISERAD DAGLIG IMPORT FÖR GOLDENSTAT
[DIV] EN STARTPUNKT - PROCESSA ALLA DIVISIONER FÖR AKTUELL SÄSONG AUTOMATISKT

Usage: python daily_import.py
"""
import os
import sys
import datetime
import json
import traceback
from pathlib import Path
from typing import Dict, List, Optional

# Import våra moduler
from smart_season_importer import SmartSeasonImporter

class AutomatedDailyImport:
    """Automatiserad daglig import med intelligent spelarmappning"""

    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = Path("import_logs")
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"daily_import_{self.timestamp}.json"

        # Huvudlogg-struktur
        self.import_log = {
            "import_id": self.timestamp,
            "start_time": datetime.datetime.now().isoformat(),
            "end_time": None,
            "status": "in_progress",
            "files_processed": [],
            "players_handled": [],
            "mappings_applied": [],
            "new_players_created": [],
            "warnings": [],
            "errors": [],
            "statistics": {
                "total_files": 0,
                "successful_files": 0,
                "failed_files": 0,
                "total_matches_imported": 0,
                "total_players_processed": 0,
                "auto_matched_high_confidence": 0,
                "auto_matched_medium_confidence": 0,
                "auto_created_with_context": 0,
                "auto_created_new": 0
            }
        }

        print(f"[START] STARTAR AUTOMATISERAD DAGLIG IMPORT {self.timestamp}")
        print(f"[LOG] Loggfil: {self.log_file}")

    def run_full_import(self):
        """Kör fullständig automatiserad import av alla divisioner för aktuell säsong"""
        try:
            # Hitta alla match-url filer i current_match_urls katalogen
            url_files = list(Path("current_match_urls").glob("*_match_urls*.txt"))

            if not url_files:
                print("[ERROR] Inga match-url filer hittades i current_match_urls katalogen")
                return

            print(f"[FILES] Hittade {len(url_files)} URL-filer att processa")
            self.import_log["statistics"]["total_files"] = len(url_files)

            # Processa varje fil
            for i, url_file in enumerate(url_files, 1):
                print(f"\\n[FILE] [{i}/{len(url_files)}] Processar {url_file.name}")
                self.process_url_file(url_file)

            # Slutför loggen
            self.finalize_import()

        except Exception as e:
            print(f"[ERROR] KRITISKT FEL: {str(e)}")
            print(traceback.format_exc())
            self.import_log["errors"].append(f"Critical error: {str(e)}")
            self.import_log["status"] = "failed"
            self.save_log()

    def process_url_file(self, url_file: Path):
        """Processa en URL-fil med smart spelarmappning"""
        # Extrahera division info från filnamnet
        file_info = self.parse_filename(url_file.name)

        try:
            print(f"  [DIV] Division: {file_info['division_id']} ({file_info['division_name']})")

            # Skapa smart importer
            smart_importer = SmartSeasonImporter("goldenstat.db")

            # Kör importen med smart player matching
            result = smart_importer.import_from_url_file_smart(
                str(url_file),
                file_info['division_id']
            )

            # Samla statistik från smart importer
            stats = smart_importer.get_import_statistics()
            self.merge_statistics(stats)

            # Logga framgångsrik import
            file_result = {
                "file": str(url_file),
                "division_id": file_info['division_id'],
                "division_name": file_info['division_name'],
                "status": "success",
                "matches_imported": result.get("matches_imported", 0),
                "players_processed": result.get("players_processed", 0),
                "processed_at": datetime.datetime.now().isoformat()
            }

            self.import_log["files_processed"].append(file_result)
            self.import_log["statistics"]["successful_files"] += 1
            self.import_log["statistics"]["total_matches_imported"] += result.get("matches_imported", 0)
            self.import_log["statistics"]["total_players_processed"] += result.get("players_processed", 0)

            print(f"  [OK] Framgång: {result.get('matches_imported', 0)} matcher, {result.get('players_processed', 0)} spelare")

        except Exception as e:
            error_msg = f"Fel vid import av {url_file.name}: {str(e)}"
            print(f"  [ERROR] {error_msg}")

            # Logga felet
            file_error = {
                "file": str(url_file),
                "division_id": file_info.get('division_id', 'unknown'),
                "status": "failed",
                "error": str(e),
                "processed_at": datetime.datetime.now().isoformat()
            }

            self.import_log["files_processed"].append(file_error)
            self.import_log["errors"].append(error_msg)
            self.import_log["statistics"]["failed_files"] += 1

    def parse_filename(self, filename: str) -> Dict[str, str]:
        """Extrahera division info från filnamnet"""
        # Exempel: t_jM8s_0341_match_urls2A.txt
        parts = filename.replace("_match_urls", "_SPLIT_").replace(".txt", "").split("_SPLIT_")

        division_id = parts[0] if parts else "unknown"
        division_name = parts[1] if len(parts) > 1 else "unknown"

        return {
            "division_id": division_id,
            "division_name": division_name,
            "original_filename": filename
        }

    def finalize_import(self):
        """Slutför importen och skriv slutlig logg"""
        self.import_log["end_time"] = datetime.datetime.now().isoformat()
        self.import_log["status"] = "completed"

        stats = self.import_log["statistics"]

        print(f"\\n[DONE] AUTOMATISERAD IMPORT SLUTFÖRD")
        print(f"[STATS] STATISTIK:")
        print(f"   • Totalt filer: {stats['total_files']}")
        print(f"   • Framgångsrika: {stats['successful_files']}")
        print(f"   • Misslyckade: {stats['failed_files']}")
        print(f"   • Totalt matcher: {stats['total_matches_imported']}")
        print(f"   • Totalt spelare: {stats['total_players_processed']}")
        print(f"   • Auto-matched (hög): {stats['auto_matched_high_confidence']}")
        print(f"   • Auto-matched (medel): {stats['auto_matched_medium_confidence']}")
        print(f"   • Med klubb-kontext: {stats['auto_created_with_context']}")
        print(f"   • Helt nya spelare: {stats['auto_created_new']}")

        if self.import_log["warnings"]:
            print(f"   • Varningar: {len(self.import_log['warnings'])}")

        if self.import_log["errors"]:
            print(f"   • Fel: {len(self.import_log['errors'])}")
            print("[ERROR] FEL UNDER IMPORT:")
            for error in self.import_log["errors"][:5]:  # Visa första 5
                print(f"     • {error}")

        self.save_log()
        print(f"[LOG] Detaljerad logg sparad: {self.log_file}")

    def merge_statistics(self, stats: dict):
        """Slå samman statistik från smart importer"""
        main_stats = self.import_log["statistics"]
        smart_stats = stats["statistics"]

        main_stats["auto_matched_high_confidence"] += smart_stats.get("auto_matched_high_confidence", 0)
        main_stats["auto_matched_medium_confidence"] += smart_stats.get("auto_matched_medium_confidence", 0)
        main_stats["auto_created_with_context"] += smart_stats.get("auto_created_with_context", 0)
        main_stats["auto_created_new"] += smart_stats.get("auto_created_new", 0)

        # Lägg till varningar och fel
        self.import_log["warnings"].extend(stats.get("warnings", []))
        self.import_log["errors"].extend(stats.get("errors", []))

    def save_log(self):
        """Spara loggen till fil"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.import_log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Kunde inte spara logg: {e}")



def main():
    """Huvudfunktion - EN STARTPUNKT FÖR ALLT"""
    print("=" * 60)
    print("[ROBOT] GOLDENSTAT AUTOMATISERAD DAGLIG IMPORT")
    print("[TARGET] Processar alla divisioner för aktuell säsong automatiskt")
    print("=" * 60)

    # Kör automatiserad import
    importer = AutomatedDailyImport()
    importer.run_full_import()

    print("\\n[FINISH] IMPORT SLUTFÖRD")


if __name__ == "__main__":
    main()