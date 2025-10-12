# API Reference

## Table of Contents
- [Store Integrations](#store-integrations)
  - [Steam Integration](#steam-integration)
  - [GOG Integration](#gog-integration)
- [External APIs](#external-apis)
  - [IGDB Integration](#igdb-integration)
  - [HowLongToBeat Integration](#howlongtobeat-integration)
- [Notion Integration](#notion-integration)
- [Data Structures](#data-structures)

---

## Store Integrations

### Steam Integration

**File**: [steam_integration.py](steam_integration.py)

#### `SteamIntegration`

Main class for Steam Web API integration.

**Constructor**:
```python
SteamIntegration(api_key: str, steamid: str)
```

**Parameters**:
- `api_key` (str): Steam Web API key from https://steamcommunity.com/dev/apikey
- `steamid` (str): 64-bit Steam ID of the user

**Methods**:

##### `get_owned_games() -> list[dict]`

Retrieves and normalizes all games owned by the user.

**Returns**: List of normalized game dictionaries
```python
[
    {
        'appid': 12345,
        'name': 'Game Title',
        'notion_store_id': 'notion_page_id'
    },
    ...
]
```

**Example**:
```python
steam = SteamIntegration(api_key="YOUR_KEY", steamid="12345678901234567")
games = steam.get_owned_games()
print(f"Found {len(games)} games")
```

##### `get_games_from_api() -> list[dict]`

Fetches raw game data from Steam API.

**API Endpoint**: `https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/`

**Returns**: Raw Steam API response
```python
[
    {
        'appid': 12345,
        'name': 'Game Title',
        'playtime_forever': 1234,
        'img_icon_url': 'hash',
        'img_logo_url': 'hash'
    },
    ...
]
```

##### `get_game_info(appid: int) -> dict | None`

Retrieves detailed information for a specific game.

**API Endpoint**: `https://store.steampowered.com/api/appdetails?appids={appid}`

**Parameters**:
- `appid` (int): Steam application ID

**Returns**: Game details or None on failure
```python
{
    'type': 'game',
    'name': 'Game Title',
    'steam_appid': 12345,
    'required_age': 0,
    'is_free': False,
    'detailed_description': '...',
    'short_description': '...',
    'header_image': 'https://...',
    'platforms': {'windows': True, 'mac': True, 'linux': False},
    'genres': [{'id': '1', 'description': 'Action'}],
    'release_date': {'coming_soon': False, 'date': 'Jan 1, 2020'}
}
```

**Error Handling**:
- Returns `None` if API call fails
- Prints error message to console
- Handles JSON parsing errors gracefully

##### `normalize_games_list(games: list) -> list[dict]`

Converts raw Steam data to normalized format.

**Parameters**:
- `games` (list): Raw game data from `get_games_from_api()`

**Returns**: List of normalized game dictionaries

**Current Implementation**:
```python
# Basic normalization (current)
{
    'appid': game['appid'],
    'name': game['name'],
    'notion_store_id': NOTION_STORE_STEAM_ID
}
```

**Recommended Enhancement** (to skip IGDB calls):
```python
# Enhanced normalization (recommended)
{
    'appid': game['appid'],
    'name': game['name'],
    'notion_store_id': NOTION_STORE_STEAM_ID,
    'platforms': ['PC (Microsoft Windows)', 'Mac', 'Linux'],  # From Steam API
    'cover_url': game_info['header_image'],                    # From Steam API
    'release_date': '2020-01-01',                              # From Steam API
    'genres': ['Action', 'Adventure']                          # From Steam API
}
```

#### Rate Limiting

**Steam Web API Official Limits**:
- **100,000 calls per day** (~1.16 calls/second)
- **Reference**: [Steam Web API Terms of Use](https://steamcommunity.com/dev/apiterms)

**Implementation**:
```python
def _rate_limit(self):
    """
    Enforce rate limiting for Steam Store API.
    Steam Web API Terms: "You are limited to one hundred thousand (100,000) calls to the Steam Web API per day"
    Using 1.0 second intervals to stay safely under the ~1.16 calls/second limit.
    """
    elapsed = time.time() - self.last_request_time
    if elapsed < self.min_request_interval:
        sleep_time = self.min_request_interval - elapsed
        print(f"⏱️ Steam rate limit: waiting {sleep_time:.1f}s (100k calls/day official limit)")
        time.sleep(sleep_time)
    self.last_request_time = time.time()
```

---

### GOG Integration

**File**: [gog_integration.py](gog_integration.py)

#### `GogIntegration`

Main class for GOG public profile API integration.

**Constructor**:
```python
GogIntegration(username: str)
```

**Parameters**:
- `username` (str): GOG public username

**Methods**:

##### `get_owned_games() -> list[dict]`

Retrieves and normalizes all games from user's GOG library.

**Returns**: List of normalized game dictionaries
```python
[
    {
        'appid': 1234567890,
        'name': 'Game Title',
        'notion_store_id': 'notion_page_id'
    },
    ...
]
```

##### `get_games_from_public_profile(page: int = 1) -> dict | None`

Fetches a single page of games from GOG profile.

**API Endpoint**: `https://www.gog.com/u/{username}/games/stats`

**Parameters**:
- `page` (int): Page number (default: 1)

**Query Parameters**:
- `sort`: "recent_playtime"
- `order`: "desc"
- `page`: Page number

**Returns**: HAL+JSON response
```python
{
    '_embedded': {
        'items': [
            {
                'id': 1234567890,
                'title': 'Game Title',
                'game': {...},
                'stats': {...}
            },
            ...
        ]
    },
    'page': 1,
    'pages': 5
}
```

**Error Handling**:
- Returns `None` on HTTP errors
- Handles JSON parsing errors
- Prints detailed error messages

##### `get_all_games_from_public_profile() -> list[dict]`

Fetches all games across all pages.

**Returns**: List of all game items from all pages

**Implementation**:
```python
# Automatically handles pagination
# Continues until no more pages available
all_games = []
page = 1
while True:
    data = get_games_from_public_profile(page)
    if has_more_pages(data):
        page += 1
    else:
        break
return all_games
```

##### `get_game_info(appid: int) -> dict | None`

Retrieves detailed information for a specific GOG game.

**API Endpoint**: `https://www.gog.com/account/gameDetails/{appid}.json`

**Parameters**:
- `appid` (int): GOG game ID

**Returns**: Game details or None
```python
{
    'id': 1234567890,
    'title': 'Game Title',
    'image': 'https://...',
    'url': 'https://...',
    'worksOn': {'Windows': True, 'Mac': True, 'Linux': True}
}
```

**Note**: This method requires authentication and may not work with public profiles.

##### `normalize_games_list(games: list) -> list[dict]`

Converts raw GOG data to normalized format.

**Parameters**:
- `games` (list): Raw game data from `get_all_games_from_public_profile()`

**Returns**: List of normalized game dictionaries

**Current Implementation**:
```python
# Basic normalization (current)
{
    'appid': game['id'],
    'name': game['title'],
    'notion_store_id': NOTION_STORE_GOG_ID
}
```

**Recommended Enhancement**:
```python
# Enhanced normalization (recommended)
{
    'appid': game['id'],
    'name': game['title'],
    'notion_store_id': NOTION_STORE_GOG_ID,
    'platforms': ['PC (Microsoft Windows)'],  # GOG is primarily PC
    'cover_url': game.get('image'),           # If available in API
    'playtime': game['stats']['playtime']     # User's playtime
}
```

---

## External APIs

### IGDB Integration

**File**: [IGDB.py](IGDB.py)

IGDB (Internet Game Database) provides comprehensive game metadata including platforms, genres, themes, release dates, and cover images.

#### Authentication

IGDB uses Twitch OAuth2 for authentication:

```python
# Automatic authentication on module import
auth = requests.post(
    f'https://id.twitch.tv/oauth2/token?'
    f'client_id={clientID}&'
    f'client_secret={secret}&'
    f'grant_type=client_credentials'
)
access_token = auth.json()['access_token']
```

**Headers**:
```python
{
    "Client-ID": IGDB_CLIENT_ID,
    "Authorization": f"Bearer {access_token}"
}
```

#### Core Functions

##### `get_game_id(name: str) -> int | None`

Retrieves IGDB game ID by name.

**Parameters**:
- `name` (str): Game title (exact match required)

**Returns**: IGDB game ID or None

**API Query**:
```
fields id; sort rating desc; where name = "{name}"; limit 1;
```

**Example**:
```python
game_id = get_game_id("The Witcher 3: Wild Hunt")
# Returns: 1942
```

##### `get_game_platforms(name: str, debug: bool = False) -> list[str] | None`

Retrieves available platforms for a game.

**Parameters**:
- `name` (str): Game title
- `debug` (bool): Enable debug output (default: False)

**Returns**: List of platform names or None
```python
['PC (Microsoft Windows)', 'PlayStation 4', 'Xbox One', 'Nintendo Switch']
```

**API Queries**:
1. Get platform IDs: `fields platforms; where name = "{name}"; limit 1;`
2. Get platform names: `fields name; limit 500;`

**Debug Output**:
```
Game Platforms: PC (Microsoft Windows), PlayStation 4, Xbox One
```

##### `get_game_release(name: str, debug: bool = False) -> str | None`

Retrieves game release date.

**Parameters**:
- `name` (str): Game title
- `debug` (bool): Enable debug output

**Returns**: Release date in YYYY-MM-DD format or None
```python
"2015-05-19"
```

**API Query**:
```
fields first_release_date; where name = "{name}"; limit 1;
```

**Date Conversion**:
```python
# IGDB returns Unix timestamp
release = datetime.fromtimestamp(data[0]['first_release_date']).strftime("%Y-%m-%d")
```

##### `get_game_genres(name: str, debug: bool = False) -> list[str] | None`

Retrieves game genres.

**Parameters**:
- `name` (str): Game title
- `debug` (bool): Enable debug output

**Returns**: List of genre names or None
```python
['Role-playing (RPG)', 'Adventure', 'Strategy']
```

**API Queries**:
1. Get genre IDs: `fields genres; where name = "{name}"; limit 1;`
2. Get genre names: `fields name;`

**Debug Output**:
```
Game Genres: Role-playing (RPG), Adventure, Strategy
```

##### `get_game_themes(name: str) -> list[str] | None`

Retrieves game themes (narrative/setting themes).

**Parameters**:
- `name` (str): Game title

**Returns**: List of theme names or None
```python
['Fantasy', 'Open world', 'Historical']
```

**API Queries**:
1. Get theme IDs: `fields themes; where name = "{name}"; limit 1;`
2. Get theme names: `fields name;`

**Note**: Themes are often combined with genres in the Notion database.

##### `get_game_modes(name: str) -> list[str] | None`

Retrieves game modes (single-player, multiplayer, etc.).

**Parameters**:
- `name` (str): Game title

**Returns**: List of game mode names or None
```python
['Single player', 'Multiplayer', 'Co-operative']
```

**API Queries**:
1. Get mode IDs: `fields game_modes; where name = "{name}"; limit 1;`
2. Get mode names: `fields name;`

##### `get_cover_link(game_id: int) -> str | None`

Retrieves high-resolution cover image URL.

**Parameters**:
- `game_id` (int): IGDB game ID (from `get_game_id()`)

**Returns**: Cover image URL or None
```python
"https://images.igdb.com/igdb/image/upload/t_cover_big/co1234.jpg"
```

**API Query**:
```
fields url; where game = {game_id};
```

**URL Transformation**:
```python
# IGDB returns thumbnail URL
raw_url = data[0]['url']  # "//images.igdb.com/igdb/image/upload/t_thumb/co1234.jpg"

# Extract image hash
key = raw_url.split('t_thumb/')[1]  # "co1234.jpg"

# Construct high-res URL
cover_url = f"https://images.igdb.com/igdb/image/upload/t_cover_big/{key}"
```

**Available Sizes**:
- `t_thumb`: Thumbnail (90x90)
- `t_cover_small`: Small (90x128)
- `t_cover_big`: Large (264x374) - **Recommended**
- `t_1080p`: Full HD (1920x1080)

##### `get_game_websites(game_id: int) -> list[dict]`

Retrieves official websites and store links.

**Parameters**:
- `game_id` (int): IGDB game ID

**Returns**: List of trusted website links
```python
[
    {'category': Platform.STEAM, 'url': 'https://store.steampowered.com/app/...'},
    {'category': Platform.GOG, 'url': 'https://www.gog.com/game/...'},
    {'category': Platform.OFFICIAL, 'url': 'https://...'}
]
```

**API Query**:
```
fields category,trusted,url; where game = {game_id};
```

**Platform Categories** (from `Platform` enum):
- `OFFICIAL (1)`: Official website
- `STEAM (13)`: Steam store page
- `GOG (17)`: GOG store page
- `EPICGAMES (16)`: Epic Games Store page
- See [IGDB.py:5-24](IGDB.py#L5-L24) for full list

##### `save_cover(game_id: int, filename: str) -> None`

Downloads and saves cover image to disk.

**Parameters**:
- `game_id` (int): IGDB game ID
- `filename` (str): Output filename (without extension)

**Output**: Saves `{filename}.jpg` in current directory

**Example**:
```python
save_cover(1942, "witcher3_cover")
# Creates: witcher3_cover.jpg
```

#### Error Handling

All IGDB functions use consistent error handling:

```python
try:
    # API call and data processing
    return data
except Exception:
    print(igdb_errors.{error_type})
    return None
```

**Error Messages** (from `igdb_errors` enum):
- `game_id`: "Failed to get Game ID"
- `release_date`: "Failed to get Release Date"
- `genres`: "Failed to get Genres"
- `themes`: "Failed to get Themes"
- `platforms`: "Failed to get Platforms"
- `game_modes`: "Failed to get Game Modes"
- `cover_link`: "Failed to find Cover Link"

#### Rate Limiting

IGDB API limits:
- **4 requests per second** (free tier)
- Consider implementing request throttling for bulk operations

**Recommended Implementation**:
```python
import time
from functools import wraps

def rate_limit(max_per_second=4):
    min_interval = 1.0 / max_per_second
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator
```

---

### HowLongToBeat Integration

**File**: [howlongtobeat_integration.py](howlongtobeat_integration.py)

Provides estimated game completion times from HowLongToBeat community data.

#### `get_timetocompelete(title: str, debug: bool = False) -> float`

Retrieves estimated hours to complete main story.

**Parameters**:
- `title` (str): Game title
- `debug` (bool): Enable debug output (default: False)

**Returns**: Hours to complete (rounded) or 0 on failure
```python
45.0  # Hours
```

**API Endpoint**: `https://howlongtobeat.com/api/search`

**Request Format**:
```python
{
    'searchType': 'games',
    'searchTerms': ['game', 'title', 'words'],  # Split by spaces
    'searchPage': 1,
    'size': 20,
    'searchOptions': {
        'games': {
            'sortCategory': 'popular',
            'rangeCategory': 'main'
        }
    }
}
```

**Response Format**:
```python
{
    'data': [
        {
            'game_id': 12345,
            'game_name': 'Game Title',
            'comp_main': 162000,      # Seconds (divide by 3600 for hours)
            'comp_plus': 216000,      # Main + Extras
            'comp_100': 324000        # Completionist
        }
    ]
}
```

**Time Conversion**:
```python
# API returns seconds, convert to hours
completion_time = round(response.json()['data'][0]["comp_main"] / 60 / 60, 0)
```

**Example**:
```python
hours = get_timetocompelete("The Witcher 3: Wild Hunt")
print(f"Main story takes {hours} hours")
# Output: Main story takes 51 hours
```

**Debug Output**:
```
Game Completion Time: 51.0
```

**Error Handling**:
- Returns `0` if game not found
- Returns `0` if API call fails
- Silently catches all exceptions

**Note**: The function name has a typo ("compelete" instead of "complete") - consider renaming for consistency.

---

## Notion Integration

**File**: [notion_integration.py](notion_integration.py)

Handles all interactions with Notion API for database operations.

#### `NotionIntegration`

Main class for Notion API operations.

**Constructor**:
```python
NotionIntegration(auth_token: str)
```

**Parameters**:
- `auth_token` (str): Notion integration token from https://www.notion.so/my-integrations

**Methods**:

##### `write_row(database_id, cover_link, title, consoles, release_date, online, genres, length, related_page_id)`

Creates a new game entry in Notion database.

**Parameters**:
- `database_id` (str): Notion database ID
- `cover_link` (str): URL to cover image
- `title` (str): Game title
- `consoles` (list[dict]): List of `{'name': 'Platform'}`
- `release_date` (str): Date in YYYY-MM-DD format
- `online` (list[dict]): List of `{'name': 'Game Mode'}`
- `genres` (list[dict]): List of `{'name': 'Genre'}`
- `length` (float): Hours to complete
- `related_page_id` (str): Notion page ID for store relation

**Database Schema**:
```python
{
    "parent": {"database_id": database_id},
    "cover": {
        "type": "external",
        "external": {"url": cover_link}
    },
    "properties": {
        "title": {"title": [{"text": {"content": title}}]},
        "Status": {"select": {"name": "Backlog"}},
        "Release Date": {"date": {"start": release_date}},
        "genre": {"multi_select": [{"name": "Action"}, ...]},
        "Console": {"multi_select": [{"name": "PC"}, ...]},
        "Online": {"multi_select": [{"name": "Single player"}, ...]},
        "Length": {"number": 45.0},
        "Store": {"relation": [{"id": related_page_id}]}
    }
}
```

**Data Cleaning**:
```python
# Removes commas from multi-select values (Notion limitation)
cleaned_genres = [{'name': genre['name'].replace(',', '')} for genre in genres]
```

**Example**:
```python
notion = NotionIntegration(auth_token="secret_...")
notion.write_row(
    database_id="abc123",
    cover_link="https://example.com/cover.jpg",
    title="The Witcher 3",
    consoles=[{'name': 'PC'}, {'name': 'PlayStation 4'}],
    release_date="2015-05-19",
    online=[{'name': 'Single player'}],
    genres=[{'name': 'RPG'}, {'name': 'Adventure'}],
    length=51.0,
    related_page_id="store_page_id"
)
```

##### `write_text(page_id, text, type='paragraph')`

Appends text block to a Notion page.

**Parameters**:
- `page_id` (str): Target page ID
- `text` (str): Text content
- `type` (str): Block type (default: 'paragraph')

**Supported Block Types**:
- `paragraph`
- `heading_1`, `heading_2`, `heading_3`
- `bulleted_list_item`, `numbered_list_item`
- `quote`, `code`

**Example**:
```python
notion.write_text(page_id, "This is a paragraph")
notion.write_text(page_id, "This is a heading", type="heading_1")
```

##### `read_text(page_id) -> list`

Retrieves all blocks from a Notion page.

**Parameters**:
- `page_id` (str): Page ID to read

**Returns**: List of block objects
```python
[
    {
        'id': 'block_id',
        'type': 'paragraph',
        'paragraph': {
            'rich_text': [
                {'type': 'text', 'text': {'content': 'Hello world'}}
            ]
        },
        'has_children': False
    },
    ...
]
```

##### `create_simple_blocks_from_content(content) -> list`

Converts Notion blocks to simplified format.

**Parameters**:
- `content` (list): Block objects from `read_text()`

**Returns**: Simplified block structure
```python
[
    {
        'id': 'block_id',
        'type': 'paragraph',
        'text': 'Hello world',
        'children': [...]  # If has_children is True
    },
    ...
]
```

**Recursive Processing**:
- Automatically handles nested blocks
- Preserves hierarchy through `children` property

##### `write_dict_to_file_as_json(content, file_name)`

Utility function to save data as JSON file.

**Parameters**:
- `content` (dict): Data to save
- `file_name` (str): Output filename

**Example**:
```python
game_data = {'title': 'Game', 'platforms': ['PC']}
notion.write_dict_to_file_as_json(game_data, 'game_data.json')
```

---

## Data Structures

### Normalized Game Object

**Purpose**: Common format used across all store integrations

**Structure**:
```python
{
    # Required fields
    'appid': int,                 # Platform-specific game ID
    'name': str,                  # Game title
    'notion_store_id': str,       # Notion relation ID for store

    # Optional fields (for optimization)
    'platforms': list[str],       # ['PC', 'PlayStation 4', ...]
    'cover_url': str,             # Direct URL to cover image
    'release_date': str,          # 'YYYY-MM-DD'
    'genres': list[str],          # ['Action', 'Adventure', ...]
    'game_modes': list[str],      # ['Single player', 'Multiplayer', ...]

    # Store-specific fields
    'playtime': int,              # Minutes played (optional)
    'achievements': dict,         # Achievement data (optional)
}
```

**Usage in Code**:
```python
# main.py - Current implementation
for game in games:
    write_game(notion, game['name'])  # Only passes title

# main.py - Optimized implementation (recommended)
for game in games:
    write_game_optimized(notion, game)  # Passes full object
```

### Notion Multi-Select Format

**Purpose**: Format for multi-select properties in Notion

**Structure**:
```python
[
    {'name': 'Option 1'},
    {'name': 'Option 2'},
    {'name': 'Option 3'}
]
```

**Constraints**:
- Names cannot contain commas (automatically cleaned by `write_row()`)
- Maximum ~100 characters per name
- Case-sensitive

**Example**:
```python
genres = [
    {'name': 'Role-playing (RPG)'},
    {'name': 'Action'},
    {'name': 'Adventure'}
]
```

### IGDB Query Format

**Purpose**: Query language for IGDB API

**Basic Syntax**:
```
fields field1,field2,...; where condition; sort field asc|desc; limit N;
```

**Examples**:
```python
# Get game ID
"fields id; where name = \"Game Title\"; limit 1;"

# Get platforms
"fields platforms; where name = \"Game Title\"; limit 1;"

# Get all genres
"fields name;"

# Get multiple fields
"fields name,first_release_date,platforms; where id = 1234;"
```

**Operators**:
- `=`: Exact match
- `!=`: Not equal
- `>`, `<`, `>=`, `<=`: Comparison
- `&`, `|`: AND, OR

### Environment Variables

**File**: `.env` (loaded by [consts.py](consts.py))

**Required Variables**:
```bash
# Notion Configuration
NOTION_TOKEN=secret_...
NOTION_DATABASE_ID=abc123...
NOTION_PAGE_ID=def456...
NOTION_STORE_STEAM_ID=steam_page_id
NOTION_STORE_GOG_ID=gog_page_id

# Steam API
STEAM_API_KEY=ABCDEF123456...
STEAM_USERID_64=76561198...

# GOG API
GOG_PUBLIC_USERNAME=your_username

# IGDB API (Twitch)
IGDB_CLIENT_ID=abc123...
IGDB_SECRET=def456...
```

**Setup Instructions**:
See [README.md](README.md) for detailed setup guide.

---

## Usage Examples

### Basic Usage

```python
# Initialize integrations
steam = SteamIntegration(api_key="...", steamid="...")
gog = GogIntegration(username="...")
notion = NotionIntegration(auth_token="...")

# Get games from stores
steam_games = steam.get_owned_games()
gog_games = gog.get_owned_games()

# Combine all games
all_games = steam_games + gog_games

# Add to Notion
for game in all_games:
    write_game(notion, game['name'])
```

### Optimized Usage (Recommended)

```python
def write_game_optimized(notion, game_data):
    """Skip IGDB calls if store already provides data"""
    title = game_data['name']

    # Use store data if available, otherwise call IGDB
    consoles = game_data.get('platforms') or handle_game_platforms(title)
    release_date = game_data.get('release_date') or handle_game_release(title)
    genres = game_data.get('genres') or handle_game_genres(title)
    online = game_data.get('game_modes') or handle_game_modes(title)
    cover = game_data.get('cover_url') or handle_game_cover(title)

    # HowLongToBeat always needed
    length = handle_game_length(title)

    notion.write_row(
        NOTION_DATABASE_ID,
        cover,
        title,
        consoles,
        release_date,
        online,
        genres,
        length,
        game_data['notion_store_id']
    )
```

### Error Handling

```python
def safe_get_game_info(integration, appid):
    """Safely retrieve game info with error handling"""
    try:
        info = integration.get_game_info(appid)
        if info is None:
            print(f"Warning: Could not fetch info for appid {appid}")
            return {}
        return info
    except Exception as e:
        print(f"Error fetching game info: {e}")
        return {}
```

### Rate Limiting

```python
import time

def process_games_with_rate_limit(games, max_per_second=4):
    """Process games with rate limiting"""
    interval = 1.0 / max_per_second

    for game in games:
        start_time = time.time()

        # Process game
        write_game(notion, game['name'])

        # Wait if needed
        elapsed = time.time() - start_time
        if elapsed < interval:
            time.sleep(interval - elapsed)
```

---

## Troubleshooting

### Common Issues

#### "Failed to get Game ID"
- **Cause**: Game name spelling/capitalization doesn't match IGDB
- **Solution**: Check exact title on IGDB website, use proper capitalization

#### "Error: 'data' key not found in response"
- **Cause**: Steam API returned invalid response
- **Solution**: Check API key validity, verify game appid exists

#### "Error: Unable to parse JSON response"
- **Cause**: API endpoint returned non-JSON data
- **Solution**: Check network connection, verify API endpoint status

#### Rate Limit Exceeded (IGDB)
- **Cause**: More than 4 requests per second to IGDB
- **Solution**: Implement rate limiting (see examples above)

### Debug Mode

Enable debug output in any function:

```python
# Enable debug for specific operations
consoles = handle_game_platforms(title, debug=True)
release_date = handle_game_release(title, debug=True)
length = get_timetocompelete(title, debug=True)
```

**Debug Output**:
```
Game Platforms: PC (Microsoft Windows), PlayStation 4, Xbox One
Game Release Date: 2015-05-19
Game Genres: Role-playing (RPG), Adventure, Strategy
Game Completion Time: 51.0
```

---

## Performance Optimization Tips

1. **Batch Operations**: Group API calls when possible
2. **Cache Results**: Store IGDB responses to avoid duplicate lookups
3. **Parallel Processing**: Use `concurrent.futures` for multiple games
4. **Skip Unnecessary Calls**: Use store-provided data when available
5. **Rate Limiting**: Implement proper throttling for API calls

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed optimization strategies.
