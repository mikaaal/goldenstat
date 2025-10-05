#!/usr/bin/env python3
"""
Test att den fixade array-importen fungerar
"""
from smart_season_importer import SmartSeasonImporter

def test_specific_match_fix():
    """Testa fix för specifik match med array-format"""
    print("=== TEST AV ARRAY-IMPORT FIX ===")

    # URL för Mjölner vs Dartanjang match
    test_url = "https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_online_t.php?cmd=get_setdata&tmid=t_jM8s_0341_lg_0_01bh_rTNf_tP9x"

    # Skapa importer
    importer = SmartSeasonImporter("goldenstat.db")

    try:
        print(f"Testar URL: {test_url}")

        # Hämta data
        response = importer.session.get(test_url, timeout=15)

        if response.status_code == 200:
            match_data_array = response.json()

            print(f"Array-länngd: {len(match_data_array)}")

            # Räkna spelare i hela arrayen
            total_players = 0
            unique_players = set()

            for i, element in enumerate(match_data_array):
                stats_data = element.get('statsData', [])
                if stats_data:
                    for team_stats in stats_data:
                        order = team_stats.get('order', [])
                        if order:  # Skippa None och tomma listor
                            for player in order:
                                name = player.get('oname', '').strip()
                                if name:
                                    total_players += 1
                                    unique_players.add(name)

            print(f"Totalt spelare i alla element: {total_players}")
            print(f"Unika spelare: {len(unique_players)}")

            print("Unika spelarnamn:")
            for name in sorted(unique_players):
                print(f"  - {name}")

            # Kolla om våra förväntade spelare finns
            expected = ["Mats Andersson", "Micke Lundberg", "Anders Mars", "Gareth Young"]
            found = []
            missing = []

            for exp in expected:
                if exp in unique_players:
                    found.append(exp)
                else:
                    missing.append(exp)

            print(f"\nFörväntade spelare hittade ({len(found)}):")
            for name in found:
                print(f"  [OK] {name}")

            if missing:
                print(f"\nSaknade spelare ({len(missing)}):")
                for name in missing:
                    print(f"  [MISSING] {name}")
            else:
                print(f"\n[SUCCESS] ALLA FÖRVÄNTADE SPELARE HITTADE!")

            # Om alla spelare finns, testa importen
            if not missing:
                print(f"\n=== TESTAR NY IMPORT-METOD ===")
                try:
                    importer.import_match_from_array_smart(match_data_array, "t_jM8s_0341")
                    print("[SUCCESS] Import lyckades!")

                    # Kontrollera resultat
                    stats = importer.get_import_statistics()
                    print(f"Spelare processade: {stats['statistics']['total_players_processed']}")

                except Exception as e:
                    print(f"[ERROR] Import misslyckades: {e}")

        else:
            print(f"HTTP fel: {response.status_code}")

    except Exception as e:
        print(f"Fel: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_specific_match_fix()