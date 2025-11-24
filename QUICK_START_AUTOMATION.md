# 🚀 Quick Start: Automatisk Daglig Import

## TL;DR - Vad händer nu?

✅ **GitHub Actions kör automatisk import varje dag kl 02:00**
✅ **Databasen lagras i Railway (persistent volume)**
✅ **Du behöver ALDRIG pusha databasen till Git igen**
✅ **Du kan fortfarande köra manuell import när du vill**

---

## 🎯 Setup (10 minuter)

### Steg 1: Railway Volume (2 min)

1. Gå till [Railway Dashboard](https://railway.app)
2. Öppna ditt projekt → din service
3. Klicka på **"Variables"** → **"Volumes"**
4. **"New Volume"**:
   - Mount Path: `/app/data`
   - Name: `goldenstat-db`

### Steg 2: Railway Environment Variables (1 min)

Lägg till i Railway Dashboard → Variables:

```
DATABASE_PATH=/app/data/goldenstat.db
```

### Steg 3: GitHub Secrets (5 min)

Hämta Railway credentials:

```bash
# Terminal
railway login
railway whoami --token  # Kopiera denna token
```

Gå till GitHub → Settings → Secrets → New repository secret:

| Secret Name | Värde | Hur du hittar det |
|-------------|-------|-------------------|
| `RAILWAY_TOKEN` | Din token | `railway whoami --token` |
| `RAILWAY_PROJECT_ID` | Project ID | URL: `railway.app/project/{PROJECT_ID}` |
| `RAILWAY_SERVICE_ID` | Service ID | URL: `...project/{PROJECT_ID}/service/{SERVICE_ID}` |

### Steg 4: Första Uppladdningen (2 min)

Ladda upp din nuvarande databas till Railway:

```bash
# Sätt environment variables (tillfälligt)
export RAILWAY_PROJECT_ID=din-project-id
export RAILWAY_SERVICE_ID=din-service-id
export RAILWAY_TOKEN=din-token

# Ladda upp databas
python scripts/railway_db_sync.py upload
```

✅ **KLART!** GitHub Actions tar över från och med nu.

---

## 📅 Hur det Fungerar Dagligen

### Automatisk Process (varje dag kl 07:00):

```
07:00 → GitHub Actions startar
07:01 → Laddar ner databas från Railway
07:02 → Kör daily_import.py
07:05 → Laddar upp uppdaterad databas
07:06 → Sparar import-logg
✅     → Klart! Appen på Railway använder nya datan
```

### Vad händer INTE:

❌ Inget nytt deploy (appen fortsätter köra)
❌ Inget commit till main (bara import-loggen)
❌ Ingen manual intervention krävs

---

## 🔧 Manuell Import (när du vill testa något)

### Alternativ 1: Trigger GitHub Actions manuellt

1. Gå till GitHub → **Actions**
2. Välj **"Daily Database Import"**
3. **"Run workflow"** → Run

### Alternativ 2: Lokal import + sync

```bash
# Kör import lokalt
python daily_import.py

# Ladda upp till Railway (om du vill)
export RAILWAY_TOKEN=...
export RAILWAY_PROJECT_ID=...
export RAILWAY_SERVICE_ID=...
python scripts/railway_db_sync.py upload
```

### Alternativ 3: Bara lokal testing

```bash
# Kör bara lokalt (påverkar inte Railway)
python daily_import.py

# Testa lokalt
python app.py
```

---

## 📊 Övervaka Import

### GitHub Actions Logs:

1. GitHub → **Actions**
2. Senaste **"Daily Database Import"** run
3. Kolla logs för varje steg

### Import Artifacts:

Varje import sparar detaljerad logg:

- GitHub Actions → Artifacts → `import-log-{nummer}`
- Eller i repo: `import_logs/daily_import_*.json`

### Visa Senaste Statistik:

```bash
# Lokalt
python -c "
import json
from glob import glob
latest = sorted(glob('import_logs/*.json'))[-1]
log = json.load(open(latest))
print(json.dumps(log['statistics'], indent=2))
"
```

---

## 🚨 Troubleshooting

### "GitHub Actions fails immediately"

**Problem:** Secrets saknas eller är felaktiga

**Fix:**
```bash
# Verifiera secrets
railway whoami
railway status

# Dubbelkolla att alla 3 secrets finns i GitHub
```

### "No database found on Railway"

**Första gången?** Detta är normalt!

**Fix:**
```bash
# Ladda upp din lokala databas
python scripts/railway_db_sync.py upload
```

### "Import runs but app shows old data"

**Problem:** Volume inte korrekt mountat

**Fix:**
1. Kolla Railway → Variables → Volumes
2. Mount path ska vara: `/app/data`
3. Environment variable: `DATABASE_PATH=/app/data/goldenstat.db`

---

## 📝 Vanliga Frågor

### Vad händer om import misslyckas?

- GitHub Actions markerar det som failed
- Du får email-notis (om du har notifications på)
- Railway-databasen påverkas INTE (den gamla finns kvar)
- Nästa dag försöker den igen

### Kan jag ändra schemat?

Ja! Editera `.github/workflows/daily-import.yml`:

```yaml
schedule:
  - cron: '0 7 * * *'  # 07:00 UTC
  # Ändra till vad du vill, t.ex.:
  - cron: '0 */6 * * *'  # Var 6:e timme
  - cron: '0 20 * * *'  # 20:00 UTC
```

### Vad kostar detta?

- **GitHub Actions:** Gratis för public repos, 2000 min/månad för private
- **Railway:** Volume storage ingår i plan (några MB för SQLite)
- **Total:** ~0 kr extra

### Kan jag stänga av automation?

Ja! Två sätt:

1. **Tillfälligt:** GitHub → Actions → Disable workflow
2. **Permanent:** Ta bort `.github/workflows/daily-import.yml`

---

## ✅ Checklista - Är Allt Konfigurerat?

- [ ] Railway volume skapad (`/app/data`)
- [ ] Railway environment variable `DATABASE_PATH` satt
- [ ] GitHub secrets satta (3st: TOKEN, PROJECT_ID, SERVICE_ID)
- [ ] Första databasen uppladdad till Railway
- [ ] GitHub Actions workflow enabled
- [ ] Test-kört manuell workflow (för att verifiera)

---

## 🎉 Du är Klar!

Från och med nu:

- ☕ **07:00 varje dag:** Data uppdateras automatiskt
- 🚀 **Railway:** Appen använder alltid senaste datan
- 📊 **GitHub:** Import-loggar sparas för insyn
- 🧘 **Du:** Behöver inte göra något!

Vid frågor, kolla `RAILWAY_SETUP.md` för mer detaljer.
