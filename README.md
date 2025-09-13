# GoldenStat - Dart Statistics Scraper

A Python-based web scraper that extracts detailed dart match data from n01darts.com and stores it in a SQLite database for statistical analysis.

## Features

- 🎯 **Complete Match Data**: Scrapes team matches, individual games, and detailed leg information
- 📊 **Detailed Statistics**: Tracks player averages, wins/losses, and performance over time
- 🎲 **Throw-by-Throw Data**: Captures every dart throw with scores and remaining points
- 🗄️ **SQLite Database**: Structured storage for easy querying and analysis
- 🚀 **Automated Scraping**: Handles JavaScript-heavy pages with Playwright

## Project Structure

```
goldenstat/
├── database.py          # Database models and operations
├── scraper.py           # Main scraping logic
├── test_scraper.py      # Test script
├── setup.py            # Installation script
├── database_schema.sql  # Database schema
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Installation

1. **Install Xcode Command Line Tools** (macOS):
   ```bash
   xcode-select --install
   ```

2. **Run the setup script**:
   ```bash
   python3 setup.py
   ```

   Or install manually:
   ```bash
   pip3 install playwright beautifulsoup4 python-dateutil requests
   playwright install chromium
   ```

## Usage

### Basic Scraping

```python
from scraper import DartScraper
import asyncio

async def main():
    scraper = DartScraper()
    match_url = "https://n01darts.com/n01/league/season.php?id=your_match_id"
    result = await scraper.scrape_match(match_url)
    print(result)

asyncio.run(main())
```

### Player Statistics

```python
from database import DartDatabase

db = DartDatabase()
stats = db.get_player_stats("Player Name")
print(f"Matches: {stats['total_matches']}")
print(f"Win rate: {stats['win_percentage']:.1f}%")
print(f"Average: {stats['average_score']}")
```

### Testing

Run the test script to verify everything works:
```bash
python3 test_scraper.py
```

## Database Schema

The scraper creates the following tables:

- **teams**: Team information and divisions
- **players**: Player names and IDs
- **matches**: Complete team matches with scores
- **sub_matches**: Individual games within a team match
- **sub_match_participants**: Links players to specific games
- **legs**: Individual legs within games
- **throws**: Every dart throw with detailed scoring

## Data Flow

1. **Match Overview**: Extracts team names, total scores, and division info
2. **Sub-Match Details**: Identifies all individual games and their MIDs
3. **Detailed Scraping**: Navigates to each game's detail page
4. **localStorage Data**: Extracts throw-by-throw data from browser storage
5. **Database Storage**: Normalizes and stores all data relationally

## Example Match URL

```
https://n01darts.com/n01/league/season.php?id=t_KQNP_2960&lg=0-W0XD&tm=lg-0_v4qb-W0XD-XbQP
```

## Development

### Key Components

- **DartScraper**: Main scraper class handling browser automation
- **DartDatabase**: Database wrapper with helper methods
- **Match Processing**: Extracts team vs team overview data
- **Sub-Match Processing**: Handles Singles/Doubles game details
- **Leg Processing**: Stores detailed throw data from localStorage

### Error Handling

The scraper includes comprehensive error handling for:
- Network timeouts
- Missing page elements
- Invalid localStorage data
- Database constraint violations

## Future Enhancements

- [ ] League-wide scraping from main league pages
- [ ] Real-time match monitoring
- [ ] Web interface for statistics viewing
- [ ] Export functionality (CSV, JSON)
- [ ] Player performance trends and analytics
- [ ] Team comparison tools

## License

MIT License - See LICENSE file for details