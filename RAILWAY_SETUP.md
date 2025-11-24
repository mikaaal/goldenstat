# Railway Setup Guide

## 🎯 Översikt

Detta projekt använder Railway med persistent volume för att lagra SQLite-databasen mellan deployments. GitHub Actions kör automatisk daglig import som synkroniserar data.

## 📦 Railway Persistent Volume Setup

### Steg 1: Skapa Volume i Railway Dashboard

1. Gå till ditt projekt i Railway Dashboard
2. Klicka på din service
3. Gå till "Variables" → "Volumes"
4. Klicka "New Volume"
5. Konfigurera:
   - **Mount Path**: `/app/data`
   - **Name**: `goldenstat-db`

### Steg 2: Sätt Environment Variables

I Railway Dashboard, lägg till följande miljövariabler:

```bash
DATABASE_PATH=/app/data/goldenstat.db
PORT=5000
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

## 🔐 GitHub Secrets Setup

För att GitHub Actions ska kunna synkronisera databasen behöver du sätta följande secrets i GitHub:

### Hitta Railway credentials:

1. **RAILWAY_TOKEN**:
   ```bash
   railway login
   railway whoami --token
   ```

2. **RAILWAY_PROJECT_ID**:
   - Gå till ditt projekt i Railway Dashboard
   - URL:en innehåller project ID: `railway.app/project/{PROJECT_ID}`
   - Eller kör: `railway status` och leta efter "Project ID"

3. **RAILWAY_SERVICE_ID**:
   - I Railway Dashboard, klicka på din service
   - URL:en innehåller service ID: `railway.app/project/{PROJECT_ID}/service/{SERVICE_ID}`
   - Eller kör: `railway status` och leta efter "Service ID"

### Lägg till i GitHub:

1. Gå till ditt GitHub repo
2. Settings → Secrets and variables → Actions
3. Klicka "New repository secret"
4. Lägg till dessa secrets:
   - `RAILWAY_TOKEN` - Din Railway API token
   - `RAILWAY_PROJECT_ID` - Ditt Railway projekt ID
   - `RAILWAY_SERVICE_ID` - Din Railway service ID

## 🤖 Automatisk Daglig Import

GitHub Actions workflow (`.github/workflows/daily-import.yml`) kör automatiskt varje dag kl 07:00 UTC.

### Workflow gör följande:

1. ✅ Laddar ner nuvarande databas från Railway
2. ✅ Kör `daily_import.py` med senaste match-data
3. ✅ Laddar upp uppdaterad databas till Railway
4. ✅ Sparar import-loggar som artifacts
5. ✅ Committar senaste loggen till repo (valfritt)

### Manuell Trigger:

Du kan köra importen manuellt:

1. Gå till GitHub → Actions
2. Välj "Daily Database Import"
3. Klicka "Run workflow"

## 📊 Övervaka Import

### Visa senaste import-logg:

```bash
# Lokalt
python -c "import json; print(json.dumps(json.load(open(sorted(__import__('glob').glob('import_logs/*.json'))[-1])), indent=2))"
```

### GitHub Actions Artifacts:

1. Gå till Actions → Senaste workflow run
2. Scroll ner till "Artifacts"
3. Ladda ner `import-log-{run_number}`

## 🔧 Lokal Utveckling

### Köra lokal import:

```bash
# Standard lokal import (använder local goldenstat.db)
python daily_import.py

# Synkronisera med Railway (kräver Railway CLI + credentials)
python scripts/railway_db_sync.py download
python daily_import.py
python scripts/railway_db_sync.py upload
```

### Railway CLI kommandon:

```bash
# Installera Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Logga in
railway login

# Kolla status
railway status

# Kolla databas storlek på Railway
railway run --service {SERVICE_ID} ls -lh /app/data/

# Kör kommando i Railway environment
railway run --service {SERVICE_ID} python -c "import sqlite3; print(sqlite3.connect('/app/data/goldenstat.db').execute('SELECT COUNT(*) FROM matches').fetchone())"
```

## 🚨 Troubleshooting

### Problem: "No database found on Railway"

**Första deployment?** Detta är normalt. GitHub Actions kommer att skapa och ladda upp databasen första gången den körs.

**Lösning:**
```bash
# Ladda upp din lokala databas till Railway
railway login
export RAILWAY_PROJECT_ID=your-project-id
export RAILWAY_SERVICE_ID=your-service-id
export RAILWAY_TOKEN=your-token
python scripts/railway_db_sync.py upload
```

### Problem: "Railway command failed"

**Kontrollera credentials:**
```bash
railway whoami
railway status
```

**Kontrollera att volume är mountat:**
```bash
railway run --service {SERVICE_ID} ls -la /app/data/
```

### Problem: GitHub Actions fails

1. Kolla att alla secrets är korrekt satta
2. Kolla Actions logs för felmeddelanden
3. Verifiera att Railway service är running

## 📈 Best Practices

### ✅ Gör detta:

- Låt GitHub Actions hantera daglig import
- Kör lokal import för testing/development
- Övervaka import-logs regelbundet
- Backup databas innan stora ändringar

### ❌ Undvik detta:

- Pusha goldenstat.db till Git (ignoreras av .gitignore)
- Köra import manuellt i produktion
- Ändra Railway volume mount path utan att uppdatera DATABASE_PATH
- Ta bort gamla import-logs (de är användbara för debugging)

## 🔄 Migration från Gammal Setup

Om du tidigare pushade databas till Git:

1. Ta bort `goldenstat.db` från Git tracking:
   ```bash
   git rm --cached goldenstat.db
   echo "goldenstat.db" >> .gitignore
   git commit -m "Remove database from Git tracking"
   ```

2. Ladda upp nuvarande databas till Railway:
   ```bash
   python scripts/railway_db_sync.py upload
   ```

3. Låt GitHub Actions ta över dagliga uppdateringar

## 📚 Mer Information

- [Railway Volumes Documentation](https://docs.railway.app/reference/volumes)
- [Railway CLI Documentation](https://docs.railway.app/develop/cli)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
