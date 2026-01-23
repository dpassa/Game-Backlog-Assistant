# Quick Start Guide

Get your game backlog synced to Notion in 5 minutes!

## Prerequisites

- Python 3.8+
- Steam/GOG account
- Notion account

## Setup (5 minutes)

### 1. Clone & Install
```bash
git clone https://github.com/dpassa/Game-Backlog-Assistant.git
cd Game-Backlog-Assistant
pip install -r requirements.txt
```

### 2. Configure Notion

**Create Integration** (2 minutes):
1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Name it "Game Backlog"
4. Copy the **Integration Token** (starts with `secret_...`)

**Set up Database** (1 minute):
1. Use this template: https://www.notion.so/templates/videogame-backlog-tracker
2. Click on the database, then "..." → "Add connections" → Select your integration
3. Copy the **Database ID** from URL: `notion.so/.../{DATABASE_ID}?v=...`

### 3. Get API Keys

**Steam** (1 minute):
1. Get API key: https://steamcommunity.com/dev/apikey
2. Get your Steam ID 64: https://steamid.io/

**GOG** (30 seconds):
- Just your public username (e.g., from `gog.com/u/YourUsername`)

**IGDB** (1 minute):
1. Create Twitch app: https://dev.twitch.tv/console/apps
2. Copy Client ID and Client Secret

### 4. Create `.env` File

Create a file named `.env` in the project folder:

```env
# Notion
NOTION_TOKEN=secret_your_token_here
NOTION_DATABASE_ID=your_database_id_here
NOTION_PAGE_ID=your_page_id_here
NOTION_STORE_STEAM_ID=steam_relation_page_id
NOTION_STORE_GOG_ID=gog_relation_page_id

# Steam
STEAM_API_KEY=your_steam_api_key
STEAM_USERID_64=your_steam_id_64

# GOG
GOG_PUBLIC_USERNAME=your_gog_username

# IGDB (Twitch)
IGDB_CLIENT_ID=your_client_id
IGDB_SECRET=your_client_secret
```

## Run (30 seconds)

### Sync All Your Games
```bash
python main.py
```

That's it! The app will:
1. Fetch all games from Steam/GOG
2. Get metadata (platforms, genres, release dates, covers)
3. Sync everything to your Notion database

### With Debug Output
```bash
python main.py --debug
```

See which data comes from Steam/GOG vs IGDB!

## Expected Output

```
Fetching games from 2 store(s)...
  Loading Steam library...
  Found 231 games in Steam
  Loading GOG library...
  Found 200 games in GOG

Total games to process: 431
🚀 Using optimized mode (skipping redundant IGDB calls)

[1/431] --- Adding The Witcher 3: Wild Hunt ---
Game Added to Database
[2/431] --- Adding Celeste ---
Game Added to Database
...

============================================================
✓ Sync completed!
============================================================
```

## Processing Time

- **Small library** (50 games): ~1 minute
- **Medium library** (150 games): ~3 minutes
- **Large library** (400+ games): ~10 minutes

*Note: First sync is slower due to Steam rate limiting. Subsequent syncs would be faster with caching (future feature).*

> **Steam API Rate Limits**: Steam Web API has an official limit of **100,000 calls per day** (approximately 1.16 calls per second). The app automatically enforces 1-second intervals between requests to stay within this limit.  
> **Reference**: [Steam Web API Terms of Use](https://steamcommunity.com/dev/apiterms)

## Troubleshooting

### "No store integrations configured"
- Check your `.env` file has Steam or GOG credentials

### "Error: 'data' key not found"
- Some games may not be available in Steam API
- This is normal, the app will continue with other games

### "HTTP 429" errors
- Rate limiting is working! The app will automatically wait
- This is expected behavior for Steam API (100,000 calls/day limit)

### "Failed to get Game ID"
- IGDB couldn't find the game (rare)
- Usually due to exact title mismatch
- Game will still be added with available data

## Next Steps

### Explore Your Database
Your Notion database now has all your games with:
- ✅ Cover images
- ✅ Platforms
- ✅ Release dates
- ✅ Genres
- ✅ Game modes
- ✅ Time to complete
- ✅ Backlog status

### Customize
- Change game status (Backlog → Playing → Completed)
- Add personal notes
- Filter by platform, genre, or status
- Sort by release date or completion time

### Advanced Usage

**Debug mode** - see optimization stats:
```bash
python main.py --debug
```

**Legacy mode** - always use IGDB (slower):
```bash
python main.py --legacy
```

**Test APIs** - explore data structures:
```bash
cd tests
python run_api_tests.py
```

## Documentation

- **[README.md](README.md)** - Full project documentation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - How it works
- **[API_TESTING_RESULTS.md](API_TESTING_RESULTS.md)** - What data we get from each API

## Support

- Issues: https://github.com/dpassa/Game-Backlog-Assistant/issues
- See documentation links above for detailed guides

---

**Happy Gaming! 🎮**
