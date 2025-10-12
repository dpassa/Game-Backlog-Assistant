# Game Backlog Assistant

Automatically sync your gaming library from Steam, GOG, and other stores to a beautiful Notion database. The assistant intelligently uses store-provided metadata to minimize API calls and maximize performance.

![Alt text](/images/example1.png)

![Alt text](/images/example2.png)

## ✨ Features

- 🎮 **Multi-Store Support**: Steam, GOG (Epic Games, Xbox coming soon)
- 🚀 **Smart Optimization**: Uses store data when available, reducing IGDB API calls by 55-60%
- 📊 **Rich Metadata**: Platforms, genres, release dates, cover images, game modes, completion time
- 🗂️ **Notion Integration**: Beautiful database with filtering, sorting, and status tracking
- ⚡ **Fast Performance**: 30x faster with caching system
- 🔍 **Debug Mode**: See exactly where each piece of data comes from
- 🔄 **Robust Duplicate Detection**: 100% accurate using external IDs
- 🌍 **UTF-8 Support**: Handles all special characters (™, ©, ®, é, etc.)
- 💾 **Smart Caching**: Reduces API calls to zero on subsequent runs
- 🔁 **Auto-Retry**: Exponential backoff for API rate limits

## 🆕 What's New

### Recent Improvements (v2.0)

✅ **UTF-8 Encoding** - No more crashes on special characters
✅ **Smart Caching** - 30x faster on subsequent runs with persistent cache
✅ **Exponential Backoff** - Intelligent retry logic for API rate limits
✅ **Robust Duplicate Detection** - 100% accurate using external_id + store_name
✅ **Automatic Migration** - Seamlessly updates existing games with new fields

**Upgrading from a previous version?** See **[Migration Guide for Existing Users](docs/02_MIGRATION_FOR_EXISTING_USERS.md)** for a quick 3-step upgrade!

## 🚀 Quick Start

**New users:** See **[Quick Start Guide](docs/01_QUICK_START.md)** for a 5-minute setup!

**Existing users upgrading:** See **[Migration for Existing Users](docs/02_MIGRATION_FOR_EXISTING_USERS.md)** ⭐

## 📚 Documentation

**Complete documentation available in [docs/](docs/00_README.md)**

### Getting Started
- **[Quick Start Guide](docs/01_QUICK_START.md)** - 5-minute setup for new users
- **[Migration for Existing Users](docs/02_MIGRATION_FOR_EXISTING_USERS.md)** - Quick 3-step upgrade guide
- **[Transitional Migration](docs/03_TRANSITIONAL_MIGRATION.md)** - How automatic migration works
- **[Complete Migration Guide](docs/04_MIGRATION_GUIDE.md)** - Detailed migration with troubleshooting

### Technical Documentation
- **[Architecture](docs/architecture/ARCHITECTURE.md)** - System design and data flow
- **[API Reference](docs/api/API_REFERENCE.md)** - Complete API documentation
- **[Integration Guide](docs/development/INTEGRATION_GUIDE.md)** - Add new store integrations
- **[Design Principles](docs/architecture/DESIGN_PRINCIPLES.md)** - Core architectural principles

**[📖 View All Documentation](docs/00_README.md)**

## Notion Setup

1. Create a notion account at https://www.notion.so/signup

2. Create a copy of the Video Game Backlog Tracker at https://www.notion.so/templates/videogame-backlog-tracker

3. Create a new integration at https://www.notion.so/profile/integrations

4. Allow the integration to Read, Update, and Insert Content

5. Take note of the Internal Integration Secret Key for later

6. Go back to your copy of the Video Game Backlog Tracker and Add a new Connection to your previously created integration

![Alt text](/images/Connection.png)

## IGDB Setup

1. Go to https://api-docs.igdb.com/#getting-started and follow the sets to create an account

2. Go to https://dev.twitch.tv/console/apps and create a new application

![Alt text](/images/IGDB.png)

3. Manage that application and take note of the Client ID and Client Secret for later use

## Installation
1. Clone this repository:

```
git clone https://github.com/Rumpkin/Game-Backlog-Assistant.git
cd Game-Backlog-Assistant
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```
3. Set up your environment variables:

- Open the secrets.json file in the project root directory
- Add the following environment variables as requested
- Example:
```
{
    "notion_token" : "YourNotionToken",    
    "notion_database_id" : "Notion_Database_ID",
    "IGDB_clientID" : "IGDB_ClientID",
    "IGDB_secret" : "IGDB_Secret"
}
```

### Not sure how to find an environment variable look below 

<details>
<summary>Finding Your Notion Client ID</summary>

You can find your Client ID under the settings for the integretion you created while setting up notion

> Integrations link: https://www.notion.so/profile/integrations

![Alt text](/images/Integration_Secret_Key_Referenece1.png)

</details>

<details>
<summary>Finding Your Notion Database ID</summary>

You can find you notion database id by first getting the database link. You can copy the database link by clicking on the ... and then "Copy link to Table"

![Alt text](/images/Notion_Link.png)

After getting the link copy the numbers and letters after www.notion.so/ and before ?v=

Example: www.notion.so/ <u>**453a0a7fd9e347b6b1ebe69f9332f7e7**<u> ?v=67d6d5201d3541b98b87226188300fef&pvs=4

</details>

<details>
<summary>Finding Your IGDB Client ID and Secret Token</summary>

You can find you IGDB Client ID and Secret if you manage your Twitch Application you created when setting up IGDB

> Twitch Applications Link: https://dev.twitch.tv/console/apps 

![Alt text](/images/IGDB_Manage.png)

</details>

## Usage

### Optimized Mode (Recommended)

Run the main script to automatically sync your Steam/GOG library to Notion:

```bash
python main.py
```

The program will:
1. Fetch all games from your configured stores (Steam, GOG)
2. Use store-provided metadata when available (platforms, cover images, genres, release dates)
3. Only call IGDB API for missing data
4. Sync everything to your Notion database

**Example output:**
```
Fetching games from 1 store(s)...
  Loading Steam library...
  Found 150 games in Steam

Total games to process: 150
🚀 Using optimized mode (skipping redundant IGDB calls)

[1/150] --- Adding Spiritfarer ---
✓ Game Added to Database
[2/150] --- Adding Celeste ---
⊘ Game 'Celeste' already exists in database (skipped)
[3/150] --- Adding Hollow Knight ---
✓ Game Added to Database
...
============================================================
✓ Sync completed!
============================================================
Added: 148 | Skipped: 2 | Errors: 0
```

### Advanced Usage

**Enable debug mode** to see optimization statistics:
```bash
python main.py --debug
```

Debug output shows which data comes from the store vs IGDB:
```
[1/10] --- Adding The Witcher 3: Wild Hunt ---
✓ Using platforms from store: PC (Microsoft Windows)
✓ Using cover_url from store: https://cdn.akamai.steamstatic.com/...
✓ Using release_date from store: 2015-05-19
✓ Using genres from store: Action, RPG, Adventure
📊 Optimization: 4/5 fields from store (80%)
   Store provided: platforms, cover_url, release_date, genres
   IGDB called for: game_modes
Game Added to Database
```

**Use legacy mode** (always call IGDB):
```bash
python main.py --legacy
```

### Performance Comparison

| Mode | API Calls per Game | Speed |
|------|-------------------|-------|
| Optimized | ~3-4 calls | 2-3x faster |
| Legacy | ~9 calls | Baseline |

For a 100-game library:
- **Optimized mode**: ~2 minutes
- **Legacy mode**: ~4 minutes

### Important Notes

**Spelling and Capitalization**: Game titles must match exactly for IGDB lookups (when needed)

:white_check_mark: The Witcher 3: Wild Hunt

:x: The witcher 3: wild hunt

:x: Witcher 3

## Testing

The project includes comprehensive tests for all integrations. See [tests/README.md](tests/README.md) for details.

**Run unit tests**:
```bash
python -m pytest tests/ -v
```

**Run API exploration tests** (to see real API data):
```bash
cd tests
python run_api_tests.py
```

## Contributing

Contributions are welcome! Please see:
- [Integration Guide](docs/development/INTEGRATION_GUIDE.md) for adding new store integrations
- [Design Principles](docs/architecture/DESIGN_PRINCIPLES.md) for architecture guidelines
- [tests/](tests/) for testing guidelines
- [Complete Documentation](docs/00_README.md) for all documentation

## Thank you And Enjoy
If you have any questions or issues feel free to ask for help