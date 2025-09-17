# Automatiserad Import och Databashantering - Implementationsplan

## Översikt
Denna lösning hanterar automatisk daglig import av dartdata till Railway-deployment med synkronisering tillbaka till GitHub för lokal utveckling.

## Arkitektur

### Produktion (Railway)
- **Databas**: PostgreSQL (Railway managed)
- **Import**: Daglig cron job kl 02:00
- **Backup**: Automatisk export-funktion

### Utveckling (Lokalt)
- **Databas**: SQLite (goldenstat.db)
- **Sync**: Manual/automatisk från Railway
- **Backup**: GitHub Actions

## Implementation

### 1. Railway Setup

#### A. Lägg till PostgreSQL Support
```python
# database.py - Uppdatera för PostgreSQL support
import os
import sqlite3
import psycopg2
import psycopg2.extras

class DartDatabase:
    def __init__(self, db_path: str = None):
        self.db_url = os.environ.get('DATABASE_URL')
        if self.db_url and self.db_url.startswith('postgresql://'):
            self.is_postgres = True
            # Uppdatera för Railway PostgreSQL format
            if self.db_url.startswith('postgresql://'):
                self.db_url = self.db_url.replace('postgresql://', 'postgres://', 1)
        else:
            self.is_postgres = False
            self.db_path = db_path or "goldenstat.db"
    
    def get_connection(self):
        if self.is_postgres:
            return psycopg2.connect(self.db_url)
        else:
            return sqlite3.connect(self.db_path)
```

#### B. Cron Import Script
```python
# cron_import.py
#!/usr/bin/env python3
"""Railway cron job för daglig import"""

import os
import logging
from datetime import datetime
from new_season_importer import NewSeasonImporter

# Alla divisions som ska importeras
DIVISIONS = [
    't_3VAf_1770', 't_4epA_9547', 't_5L4C_6247', 't_JIvx_1896', 
    't_NcAX_0028', 't_OFlR_9185', 't_RY0l_0196', 't_UGYN_2596',
    't_Wjxm_8120', 't_XtZU_4873', 't_Y2RR_6468', 't_bmWG_5842',
    't_fWIc_3015', 't_jM8s_0341', 't_rqTc_6259', 't_v6Vw_6773',
    't_xo0C_7058'
]

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"🎯 Starting daily import at {datetime.now()}")
    
    success_count = 0
    error_count = 0
    
    for division_id in DIVISIONS:
        try:
            logger.info(f"Processing division: {division_id}")
            importer = NewSeasonImporter()
            
            # Generera URLs och importera (utan fil-beroende)
            result = importer.import_division_dynamic(division_id)
            
            logger.info(f"✅ {division_id}: {result.get('matches_imported', 0)} matches")
            success_count += 1
            
        except Exception as e:
            logger.error(f"❌ {division_id}: {str(e)}")
            error_count += 1
    
    logger.info(f"🏁 Import complete: {success_count} success, {error_count} errors")

if __name__ == "__main__":
    main()
```

#### C. Database Export Endpoint
```python
# Lägg till i app.py
import subprocess
import tempfile
from flask import Response

@app.route('/admin/export-db')
def export_database():
    """Export database för lokal utveckling"""
    try:
        if os.environ.get('DATABASE_URL'):
            # PostgreSQL export
            result = subprocess.run([
                'pg_dump', 
                '--no-owner', 
                '--no-privileges',
                os.environ['DATABASE_URL']
            ], capture_output=True, text=True, check=True)
            
            content = result.stdout
            filename = f'goldenstat_export_{datetime.now().strftime("%Y%m%d")}.sql'
            
        else:
            # SQLite export (för lokal utveckling)
            result = subprocess.run([
                'sqlite3', 'goldenstat.db', '.dump'
            ], capture_output=True, text=True, check=True)
            
            content = result.stdout
            filename = 'goldenstat_local.sql'
        
        return Response(
            content,
            mimetype='application/sql',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'application/sql'
            }
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/db-status')
def database_status():
    """Visa databas-status och statistik"""
    try:
        with sqlite3.connect(db.db_path) if not os.environ.get('DATABASE_URL') else psycopg2.connect(os.environ['DATABASE_URL']) as conn:
            cursor = conn.cursor()
            
            # Räkna antal poster per tabell
            cursor.execute("SELECT COUNT(*) FROM matches")
            matches = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM players") 
            players = cursor.fetchone()[0]
            
            cursor.execute("SELECT MAX(scraped_at) FROM matches")
            last_import = cursor.fetchone()[0]
            
        return jsonify({
            'database_type': 'PostgreSQL' if os.environ.get('DATABASE_URL') else 'SQLite',
            'matches': matches,
            'players': players, 
            'last_import': str(last_import),
            'status': 'healthy'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500
```

### 2. Railway Configuration

#### A. Environment Variables
```bash
# Railway Dashboard → Variables
DATABASE_URL=postgresql://...  # Auto-satt av Railway
CRON_ENABLED=true
DEBUG=false
```

#### B. Cron Job Setup
```bash
# Railway Dashboard → Cron Jobs
# Schedule: "0 2 * * *" (02:00 daily)
# Command: python3 cron_import.py
```

### 3. GitHub Actions för Backup

```yaml
# .github/workflows/sync-database.yml
name: Database Sync
on:
  schedule:
    - cron: '0 4 * * *'  # 04:00 - Efter Railway import
  workflow_dispatch:

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        
      - name: Download Railway database export
        run: |
          curl -L "${{ secrets.RAILWAY_APP_URL }}/admin/export-db" \
               -o railway_export.sql
               
      - name: Convert PostgreSQL dump to SQLite
        run: |
          # Installera verktyg för konvertering
          pip install sqlite3
          
          # Skapa ny SQLite databas från PostgreSQL dump
          python3 -c "
          import sqlite3
          import re
          
          # Läs PostgreSQL dump och konvertera till SQLite
          with open('railway_export.sql', 'r') as f:
              content = f.read()
          
          # Enkla konverteringar (kan behöva utökas)
          content = re.sub(r'SERIAL', 'INTEGER PRIMARY KEY AUTOINCREMENT', content)
          content = re.sub(r'TIMESTAMP', 'DATETIME', content)
          
          # Skriv till SQLite
          conn = sqlite3.connect('goldenstat.db')
          conn.executescript(content)
          conn.close()
          "
          
      - name: Commit updated database
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add goldenstat.db
          git commit -m "Auto-update database from Railway $(date)"
          git push
```

### 4. Lokal Utveckling

#### A. Sync Script
```bash
#!/bin/bash
# sync-db.sh - Hämta senaste data för lokal utveckling

echo "🔄 Syncing database from Railway..."

# Hämta export från Railway
curl -L "https://your-app.railway.app/admin/export-db" -o railway_export.sql

# Backup befintlig lokal databas
cp goldenstat.db goldenstat.db.backup

# Importera ny data
sqlite3 goldenstat.db < railway_export.sql

echo "✅ Database synced successfully!"
```

#### B. Development Workflow
```bash
# Daglig utveckling
./sync-db.sh  # Hämta senaste data
python3 app.py  # Starta lokal utveckling

# Före push till GitHub
git add .
git commit -m "Feature: xyz"
git push  # Triggar automatisk deploy till Railway
```

### 5. Monitoring och Underhåll

#### A. Log Monitoring
```python
# Lägg till i cron_import.py
import sentry_sdk  # För error tracking

# Railway logs via dashboard eller CLI
railway logs --service your-service
```

#### B. Health Checks
```python
# health_check.py - Kör som Railway cron job
def check_import_health():
    """Kontrollera att importen fungerar"""
    # Kolla senaste import-tid
    # Skicka alert om > 25 timmar sedan senaste import
    pass
```

## Användning

### För Production (Railway)
1. **Deploy**: Push till GitHub → Railway auto-deploy
2. **Import**: Automatisk kl 02:00 varje natt
3. **Monitor**: Kolla `/admin/db-status` för hälsa

### För Development (Lokalt)
1. **Sync**: Kör `./sync-db.sh` för senaste data
2. **Develop**: Använd lokal SQLite som vanligt
3. **Deploy**: Push till GitHub när klar

### För Backup
1. **Auto**: GitHub Actions skapar backup kl 04:00
2. **Manual**: Besök `/admin/export-db` för direkt export
3. **Restore**: Använd export-fil för att återställa

## Filstruktur
```
goldenstat/
├── cron_import.py          # Railway import job
├── sync-db.sh              # Lokal sync script  
├── database.py             # Uppdaterad för PostgreSQL
├── app.py                  # Med export endpoints
├── .github/workflows/
│   └── sync-database.yml   # Auto backup
└── goldenstat.db           # Lokal SQLite (synkad)
```

## Implementationsordning

### Steg 1: Database Support
1. Uppdatera `database.py` för PostgreSQL support
2. Lägg till `psycopg2` i `requirements.txt`
3. Testa lokalt med SQLite

### Steg 2: Railway Setup
1. Lägg till PostgreSQL service i Railway
2. Skapa `cron_import.py`
3. Lägg till export endpoints i `app.py`
4. Konfigurera environment variables

### Steg 3: Automatisering
1. Skapa cron job i Railway dashboard
2. Skapa `sync-db.sh` för lokal utveckling
3. Sätt upp GitHub Actions för backup

### Steg 4: Testing & Monitoring
1. Testa manuell import
2. Testa export/sync funktionalitet
3. Sätt upp logging och monitoring
4. Dokumentera troubleshooting

## Troubleshooting

### Common Issues
- **PostgreSQL connection**: Kontrollera DATABASE_URL format
- **Cron job fails**: Kolla Railway logs och dependencies
- **Export timeout**: Lägg till pagination för stora databaser
- **Sync script fails**: Kontrollera network connectivity och URL

### Debug Commands
```bash
# Railway logs
railway logs --service your-service

# Test database connection
railway run python3 -c "from database import DartDatabase; db = DartDatabase(); print('OK')"

# Manual cron test
railway run python3 cron_import.py

# Test export endpoint
curl -I https://your-app.railway.app/admin/db-status
```

Denna lösning ger dig:
- ✅ Automatisk daglig import på Railway
- ✅ Enkel synkronisering för lokal utveckling  
- ✅ Automatisk backup till GitHub
- ✅ Flexibilitet mellan SQLite och PostgreSQL
- ✅ Monitoring och felsökning