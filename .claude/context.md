# Goldenstat Project Context

## Project Overview
Goldenstat är en Flask-baserad webbapplikation för sportstatistik och dataanalys.

## Tech Stack
- **Backend**: Python Flask
- **Frontend**: HTML, CSS, JavaScript
- **Databas**: SQLite (troligtvis baserat på permissions)
- **Styling**: Custom CSS med responsiv design
- **Data Processing**: Python scripts för dataextrahering

## Project Structure
```
goldenstat/
├── app.py                          # Main Flask application
├── templates/
│   ├── base.html                   # Base template med navigation
│   └── index.html                  # Home page
├── static/
│   ├── css/
│   │   └── style.css              # Main stylesheet
│   ├── js/
│   │   └── app.js                 # Frontend JavaScript
│   └── images/
│       ├── gr.png                 # Static images
│       └── gr2.gif
├── quick_superligan_extract.py     # Data extraction script
├── reverse_engineer_schedule.py   # Schedule processing
├── import_division.sh             # Division import script
└── install_and_run.sh            # Setup script
```

## Development Environment
- **Python**: python3 (används för Flask och data processing)
- **Package Manager**: pip3 för Python dependencies
- **Browser Testing**: Playwright för automatiserad testning
- **Version Control**: Git med GitHub integration
- **Local Server**: Kör på localhost:8080
- **Data Source**: dartstatistik.se (baserat på WebFetch permissions)

## Development Preferences
- **Code Style**: Python PEP 8 standards
- **Commit Messages**: Engelska, beskrivande meddelanden
- **Error Handling**: Robust felhantering för dataextrahering
- **Performance**: Timeout-begränsningar för långvariga operationer (120-300s)
- **Security**: Begränsade permissions via settings.local.json

## Common Workflows
1. **Development Server**: 
   ```bash
   python3 app.py
   # eller via install script
   ./install_and_run.sh
   ```

2. **Data Processing**:
   ```bash
   timeout 120 python3 quick_superligan_extract.py
   timeout 300 python3 reverse_engineer_schedule.py
   ```

3. **Database Operations**:
   ```bash
   sqlite3 [database_file]
   ./import_division.sh
   ```

## Key Features
- Sportstatistik dashboard
- Dataextrahering från externa källor
- Responsiv webbgränssnitt
- Automatiserad dataprocessing med timeouts
- Säker filhantering och permissions

## Notes
- Använder timeout för långvariga operationer (säkerhet)
- WebFetch endast tillåtet för dartstatistik.se
- Docker-support tillgängligt
- Playwright för end-to-end testing
- GitHub integration för version control

## Troubleshooting
- Kontrollera port conflicts med `lsof` och `kill` kommandon
- Process management med `pkill` om nödvändigt
- Git operations fullt supportade (add, commit, push, reset, restore)
- Xcode command line tools krävs för vissa dependencies
