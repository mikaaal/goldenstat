import os
import re

# Aktiva filer som används i produktion
ACTIVE_FILES = {
    'app.py': 'AKTIV - Huvudapplikation (Flask server)',
    'database.py': 'AKTIV - Databashantering',
    'daily_import.py': 'AKTIV - Daglig import av nya matcher',
    'new_season_importer.py': 'AKTIV - Import av nya säsonger',
    'smart_season_importer.py': 'AKTIV - Smart import med mappningar',
    'single_file_import.py': 'AKTIV - Import av enskilda filer',
    'fix_player_averages.py': 'AKTIV - Fix för pilsnitt (används vid behov)',
    'generate_match_urls.py': 'AKTIV - Generera match-URLer för import',
    'requirements.txt': 'AKTIV - Python dependencies',
    'cookies.txt': 'AKTIV - Cookies för nakka-inloggning',
    'goldenstat.db': 'AKTIV - Huvuddatabas',
}

ACTIVE_DIRS = {
    'static/': 'AKTIV - Frontend assets',
    'templates/': 'AKTIV - HTML templates',
    'import_logs/': 'AKTIV - Importloggar',
    '2025-2026/': 'KAN ARKIVERAS - Match URLs (används vid import)',
    'matchurls/': 'KAN ARKIVERAS - Gamla match URLs',
}

# Kategorier
categories = {
    'AKTIV': [],
    'DEBUG/TEST': [],
    'MAPPING_VERKTYG': [],
    'GAMLA_FIXAR': [],
    'DOKUMENTATION': [],
    'CONFIG': [],
}

# Läs alla filer
for root, dirs, files in os.walk('.'):
    # Skippa vissa mappar
    if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', '.claude']):
        continue
    
    for file in files:
        filepath = os.path.join(root, file)
        filepath = filepath.replace('\', '/')
        
        # Kategorisera
        if file in ACTIVE_FILES:
            categories['AKTIV'].append((filepath, ACTIVE_FILES[file]))
        elif filepath.startswith('./static/') or filepath.startswith('./templates/'):
            categories['AKTIV'].append((filepath, 'Frontend'))
        elif filepath.startswith('./import_logs/'):
            categories['AKTIV'].append((filepath, 'Import log'))
        elif file.endswith('.md'):
            categories['DOKUMENTATION'].append((filepath, 'Dokumentation'))
        elif file in ['requirements.txt', 'cookies.txt']:
            categories['CONFIG'].append((filepath, 'Config'))
        elif 'test_' in file or 'debug_' in file or 'check_' in file or 'verify_' in file:
            categories['DEBUG/TEST'].append((filepath, 'Test/debug script'))
        elif 'player_name_mapping/' in filepath:
            categories['MAPPING_VERKTYG'].append((filepath, 'Mappningsverktyg'))
        elif any(x in file for x in ['fix_', 'cleanup_', 'analyze_', 'find_', 'map_', 'merge_', 'detect_']):
            categories['GAMLA_FIXAR'].append((filepath, 'Engångsfix/analys'))
        elif file.endswith(('.txt', '.json')) and 'match_url' in file:
            categories['GAMLA_FIXAR'].append((filepath, 'Match URL fil (kan arkiveras)'))
        elif file.endswith('.json'):
            categories['GAMLA_FIXAR'].append((filepath, 'Data fil'))
        else:
            categories['GAMLA_FIXAR'].append((filepath, 'Okategoriserad'))

# Skriv ut resultat
for cat, files in categories.items():
    if files:
        print(f'\n{"="*80}')
        print(f'{cat} ({len(files)} filer)')
        print("="*80)
        for filepath, desc in sorted(files):
            print(f'{filepath:60} - {desc}')

print(f'\n{"="*80}')
print('SAMMANFATTNING')
print("="*80)
for cat, files in categories.items():
    print(f'{cat:20} {len(files):4} filer')

