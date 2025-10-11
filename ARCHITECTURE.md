# Game Backlog Assistant - Architecture Documentation

## Overview

The Game Backlog Assistant is a Python-based application that synchronizes game libraries from various digital distribution platforms (Steam, GOG, etc.) into a Notion database. The system enriches game data with metadata from IGDB (Internet Game Database) and HowLongToBeat APIs, providing a unified view of your gaming backlog.

## Architecture Principles

### 1. Store Integration Protocol

All store integrations follow the `StoreIntegrationProtocol` defined in [store_integration_protocol.py](store_integration_protocol.py):

```python
class StoreIntegrationProtocol(Protocol):
    def get_owned_games(self) -> list[NormalizedGame]
```

**Key Design Principle**: Each integration is responsible for fetching AND normalizing its own data internally. The integration should extract all available metadata from the store's API and return fully normalized game objects. There's no separate `get_game_info()` method in the protocol - all data fetching and normalization happens inside `get_owned_games()`.

This simple, single-method protocol ensures consistent output across all store integrations while keeping each integration self-contained and easy to implement.

### 2. Data Normalization Strategy

Each store integration normalizes its data into a common format before insertion into Notion:

```python
{
    'appid': int,              # Platform-specific game ID
    'name': str,               # Game title
    'notion_store_id': str,    # Notion relation ID for the store
    # Optional fields that can skip IGDB API calls:
    'platforms': list,         # Platform availability
    'cover_url': str,          # Cover image URL
    'release_date': str,       # Release date (YYYY-MM-DD)
    'genres': list,            # Game genres
    'game_modes': list,        # Multiplayer/Singleplayer modes
}
```

**Key Optimization**: If a store provides rich metadata (platforms, cover images, genres, etc.), these fields should be included in the normalized output to **skip unnecessary IGDB API calls**.

### 3. Data Flow

```
┌─────────────────┐
│  Steam / GOG    │
│  Integration    │
└────────┬────────┘
         │ get_owned_games()
         ├─> normalize_games_list()
         │
         v
┌─────────────────┐
│  Normalized     │
│  Game Data      │
└────────┬────────┘
         │
         v
┌─────────────────┐      ┌──────────────────┐
│   main.py       │─────>│  IGDB API        │
│   write_game()  │      │  (if needed)     │
└────────┬────────┘      └──────────────────┘
         │                        │
         │<───────────────────────┘
         v                    (enrichment)
┌─────────────────┐      ┌──────────────────┐
│  Notion         │      │  HowLongToBeat   │
│  Integration    │<─────│  API             │
└─────────────────┘      └──────────────────┘
```

## Core Components

### 1. Store Integrations

#### Steam Integration ([steam_integration.py](steam_integration.py))

**API Endpoint**: Steam Web API
- `GetOwnedGames`: Retrieves user's game library
- `appdetails`: Gets detailed game information

**Rate Limiting**: 100,000 calls/day (~1.16 calls/second) - [Official Terms](https://steamcommunity.com/dev/apiterms)

**Normalized Output**:
```python
{
    'appid': game['appid'],
    'name': game['name'],
    'notion_store_id': NOTION_STORE_STEAM_ID
}
```

**Optimization Opportunities**:
- Steam's `appdetails` endpoint provides: platforms, genres, release_date, header_image
- These should be extracted in `normalize_games_list()` to avoid IGDB calls

#### GOG Integration ([gog_integration.py](gog_integration.py))

**API Endpoint**: GOG Public Profile API
- Fetches games from public user profile with pagination
- Uses session management for API consistency

**Normalized Output**:
```python
{
    'appid': game['id'],
    'name': game['title'],
    'notion_store_id': NOTION_STORE_GOG_ID
}
```

**Optimization Opportunities**:
- GOG API can provide cover images and platform information
- Extract all available metadata within `get_owned_games()` method

### 2. External Data Enrichment

#### IGDB Integration ([IGDB.py](IGDB.py))

Provides game metadata when store APIs don't offer sufficient information:

| Function | Purpose | Return Value |
|----------|---------|--------------|
| `get_game_id(name)` | Get IGDB game ID | `int` |
| `get_game_platforms(name)` | Get available platforms | `list[str]` |
| `get_game_release(name)` | Get release date | `str (YYYY-MM-DD)` |
| `get_game_genres(name)` | Get genres | `list[str]` |
| `get_game_themes(name)` | Get themes | `list[str]` |
| `get_game_modes(name)` | Get game modes | `list[str]` |
| `get_cover_link(game_id)` | Get cover image URL | `str (URL)` |

**Authentication**: Uses Twitch OAuth for IGDB access  
**Rate Limiting**: 4 requests per second (free tier)

#### HowLongToBeat Integration ([howlongtobeat_integration.py](howlongtobeat_integration.py))

Provides estimated game completion time:
- `get_timetocompelete(title)`: Returns hours to complete (main story)

### 3. Notion Integration ([notion_integration.py](notion_integration.py))

Manages database operations with Notion API:

**Key Method**: `write_row(database_id, cover_link, title, consoles, release_date, online, genres, length, related_page_id)`

**Database Schema**:
| Property | Type | Description |
|----------|------|-------------|
| title | Title | Game name |
| Status | Select | Backlog/Playing/Completed |
| Release Date | Date | Game release date |
| genre | Multi-select | Genres and themes |
| Console | Multi-select | Available platforms |
| Online | Multi-select | Game modes |
| Length | Number | Hours to complete |
| Store | Relation | Link to store page |
| Cover | Cover | Game cover image |

### 4. Main Orchestrator ([main.py](main.py))

Coordinates the entire data pipeline:

```python
def write_game(notion, title, debug=False):
    # 1. Get platforms from IGDB
    consoles = handle_game_platforms(title, debug)

    # 2. Get release date from IGDB
    release_date = handle_game_release(title, debug)

    # 3. Get genres/themes from IGDB
    genres = handle_game_genres(title, debug)

    # 4. Get game modes from IGDB
    online = handle_game_modes(title)

    # 5. Get cover image from IGDB
    cover = handle_game_cover(title)

    # 6. Get completion time from HowLongToBeat
    length = handle_game_length(title)

    # 7. Write to Notion
    notion.write_row(...)
```

**Current Limitation**: Always calls IGDB APIs regardless of whether store already provided the data.

## Configuration ([consts.py](consts.py))

All API credentials and configuration are stored in environment variables (loaded via `.env`):

```python
# Store Credentials
STEAM_API_KEY
STEAM_USERID_64
GOG_PUBLIC_USERNAME

# Notion Configuration
NOTION_TOKEN
NOTION_DATABASE_ID
NOTION_PAGE_ID
NOTION_STORE_STEAM_ID
NOTION_STORE_GOG_ID

# IGDB Credentials
IGDB_CLIENT_ID
IGDB_SECRET
```

## Optimization Strategy

### Problem: Redundant API Calls

Currently, the system always calls IGDB APIs even when the store integration already provides the necessary data.

### Solution: Conditional Enrichment

Modify the data flow to check for existing data before calling external APIs:

```python
def write_game_optimized(notion, game_data, debug=False):
    """
    game_data: Normalized game data from store integration
    Should include optional fields: platforms, cover_url, release_date, genres, etc.
    """
    title = game_data['name']

    # Only call IGDB if data is missing
    consoles = game_data.get('platforms') or handle_game_platforms(title, debug)
    release_date = game_data.get('release_date') or handle_game_release(title, debug)
    genres = game_data.get('genres') or handle_game_genres(title, debug)
    online = game_data.get('game_modes') or handle_game_modes(title)
    cover = game_data.get('cover_url') or handle_game_cover(title)

    # HowLongToBeat is always needed (no store provides this)
    length = handle_game_length(title)

    notion.write_row(...)
```

### Implementation Steps

1. **Enhance Store Integrations**:
   - Modify `normalize_games_list()` to extract all available metadata
   - Add fields to normalized output: `platforms`, `cover_url`, `release_date`, `genres`, `game_modes`

2. **Update Main Flow**:
   - Change `main()` to pass full game objects instead of just titles
   - Modify `write_game()` to accept normalized game data
   - Add conditional checks before calling IGDB APIs

3. **Steam Integration Enhancement** ([steam_integration.py](steam_integration.py:37)):
   ```python
   def normalize_games_list(self, games):
       normalized_games = []
       for game in games:
           game_info = self.get_game_info(game['appid'])
           normalized_game = {
               'appid': game['appid'],
               'name': game['name'],
               'notion_store_id': NOTION_STORE_STEAM_ID,
               # Extract from Steam API:
               'platforms': self._extract_platforms(game_info),
               'cover_url': game_info.get('header_image') if game_info else None,
               'release_date': self._extract_release_date(game_info),
               'genres': self._extract_genres(game_info),
           }
           normalized_games.append(normalized_game)
       return normalized_games
   ```

4. **GOG Integration Enhancement** ([gog_integration.py](gog_integration.py:80)):
   ```python
   def normalize_games_list(self, games):
       normalized_games = []
       for game in games:
           normalized_game = {
               'appid': game['id'],
               'name': game['title'],
               'notion_store_id': NOTION_STORE_GOG_ID,
               # Extract from GOG API:
               'cover_url': game.get('image'),  # If available in response
               'platforms': ['PC (Microsoft Windows)'],  # GOG is PC-only
           }
           normalized_games.append(normalized_game)
       return normalized_games
   ```

## Adding New Store Integrations

To add support for a new game store (e.g., Epic Games, Xbox):

1. Create a new file: `{store}_integration.py`
2. Implement `StoreIntegrationProtocol`:
   ```python
   class EpicGamesIntegration(StoreIntegrationProtocol):
       def __init__(self, credentials):
           # Initialize API client
           pass

       def get_owned_games(self) -> list[NormalizedGame]:
           """
           Fetch games from API and return normalized data.
           All data fetching and normalization happens here.
           """
           # 1. Fetch raw games from API
           raw_games = self._fetch_from_api()

           # 2. Normalize each game and extract all available metadata
           normalized_games = []
           for game in raw_games:
               normalized_game = {
                   'appid': game['id'],
                   'name': game['title'],
                   'notion_store_id': NOTION_STORE_EPIC_ID,
                   # Extract all available metadata to skip IGDB calls
                   'platforms': self._extract_platforms(game),
                   'cover_url': self._extract_cover(game),
                   'release_date': self._extract_release_date(game),
                   'genres': self._extract_genres(game),
                   'game_modes': self._extract_game_modes(game),
               }
               # Remove None values
               normalized_game = {k: v for k, v in normalized_game.items() if v is not None}
               normalized_games.append(normalized_game)

           return normalized_games
   ```
3. Add store credentials to [consts.py](consts.py) and `.env`
4. Add Notion store relation ID: `NOTION_STORE_{STORE}_ID`
5. Register integration in [main.py](main.py:77):
   ```python
   if EPIC_CREDENTIALS:
       integrations.append(EpicGamesIntegration(credentials=EPIC_CREDENTIALS))
   ```

## Error Handling

### IGDB Errors
- All IGDB functions gracefully handle failures by returning `None`
- [main.py](main.py:19) provides fallback values (e.g., current date for missing release dates)

### Store API Errors
- Network failures return `None` with error messages printed to console
- Missing game data is handled by checking for `None` values

### Notion API Errors
- Currently not handled explicitly
- Consider adding try-except blocks in `write_row()` for resilience

## Testing

Test files are located in `tests/`:
- [test_steam_integration.py](tests/test_steam_integration.py)
- [test_gog_integration.py](tests/test_gog_integration.py)
- [test_howlongtobeat_integration.py](tests/test_howlongtobeat_integration.py)

**Test Coverage Needed**:
- Normalization logic
- Conditional IGDB calls
- Error handling scenarios

## Performance Considerations

### Current Bottlenecks
1. **Sequential Processing**: Games are processed one at a time
2. **Redundant API Calls**: IGDB is always called even when data exists
3. **No Caching**: Repeated lookups for the same game

### Recommended Improvements
1. **Parallel Processing**: Use `concurrent.futures` to process multiple games simultaneously
2. **Implement Caching**: Cache IGDB responses to avoid duplicate lookups
3. **Batch Operations**: Group Notion API calls to reduce overhead
4. **Rate Limiting**: Add exponential backoff for API failures

## Future Enhancements

1. **Duplicate Detection**: Check if game already exists in Notion before adding
2. **Update Mechanism**: Sync changes in game status/metadata back to stores
3. **Additional Stores**: Epic Games, Xbox Game Pass, PlayStation Network
4. **Web Interface**: Replace CLI with web UI for better UX
5. **Database Migration**: Support other database backends (Airtable, SQLite)

## Conclusion

This architecture provides a flexible, extensible foundation for managing game backlogs across multiple platforms. The protocol-based design ensures consistency while allowing each integration to leverage platform-specific features. By implementing the proposed optimization strategy, the system can significantly reduce API calls and improve performance while maintaining data quality.
