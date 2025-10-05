#!/usr/bin/env python3
"""
Test the updated title case logic
"""
from player_mapping_manager import PlayerMappingManager

def test_title_case():
    manager = PlayerMappingManager()
    
    test_cases = [
        ("bernt andersson", "Bernt Andersson"),
        ("BERNT ANDERSSON", "Bernt Andersson"),
        ("bernt andersson", "bernt ANDERSSON"),
        ("john", "John Smith"),
        ("john smith", "john"),
        ("David Ledan", "david ledan"),
    ]
    
    print("🧪 Testing title case canonical name selection:")
    
    for name1, name2 in test_cases:
        canonical, source = manager.choose_canonical_name(name1, name2)
        print(f"  '{name1}' + '{name2}' → canonical: '{canonical}', source: '{source}'")

if __name__ == "__main__":
    test_title_case()