# Integration Guide

This guide provides step-by-step instructions for adding new store integrations and optimizing existing ones to skip unnecessary IGDB API calls.

## Table of Contents
1. [Adding a New Store Integration](#adding-a-new-store-integration)
2. [Optimizing Existing Integrations](#optimizing-existing-integrations)
3. [Data Normalization Best Practices](#data-normalization-best-practices)
4. [Testing Your Integration](#testing-your-integration)
5. [Examples: Popular Store APIs](#examples-popular-store-apis)

---

## Adding a New Store Integration

### Step 1: Create Integration File

Create a new file: `{store_name}_integration.py`

**Template**:
```python
import requests
from store_integration_protocol import StoreIntegrationProtocol
from consts import NOTION_STORE_{STORE}_ID

class {StoreName}Integration(StoreIntegrationProtocol):
    def __init__(self, credentials):
        """
        Initialize the integration with necessary credentials.

        Args:
            credentials: API key, username, or authentication object
        """
        self.credentials = credentials
        self.session = requests.Session()

    def get_owned_games(self) -> list:
        """
        Fetch and normalize all owned games.

        Returns:
            List of normalized game dictionaries
        """
        raw_games = self._fetch_games_from_api()
        return self.normalize_games_list(raw_games)

    def _fetch_games_from_api(self) -> list:
        """
        Internal method to fetch raw game data from store API.

        Returns:
            Raw API response data
        """
        # Implement API call here
        pass

    def get_game_info(self, appid: int) -> dict:
        """
        Fetch detailed information for a specific game.

        Args:
            appid: Platform-specific game identifier

        Returns:
            Detailed game information or None on failure
        """
        # Implement detailed game info fetch
        pass

    def normalize_games_list(self, games: list) -> list:
        """
        Convert raw store data to normalized format.

        Args:
            games: Raw game data from API

        Returns:
            List of normalized game dictionaries following the standard format
        """
        normalized_games = []
        for game in games:
            # Extract all available metadata
            game_info = self.get_game_info(game['id']) if 'id' in game else None

            normalized_game = {
                # Required fields
                'appid': game['id'],
                'name': game['title'],
                'notion_store_id': NOTION_STORE_{STORE}_ID,

                # Optional fields (populate when available to skip IGDB calls)
                'platforms': self._extract_platforms(game_info),
                'cover_url': self._extract_cover_url(game_info),
                'release_date': self._extract_release_date(game_info),
                'genres': self._extract_genres(game_info),
                'game_modes': self._extract_game_modes(game_info),
            }

            # Remove None values
            normalized_game = {k: v for k, v in normalized_game.items() if v is not None}
            normalized_games.append(normalized_game)

        return normalized_games

    def _extract_platforms(self, game_info: dict) -> list[str] | None:
        """Extract platform names from game info"""
        if not game_info:
            return None
        # Implement platform extraction
        pass

    def _extract_cover_url(self, game_info: dict) -> str | None:
        """Extract cover image URL from game info"""
        if not game_info:
            return None
        # Implement cover extraction
        pass

    def _extract_release_date(self, game_info: dict) -> str | None:
        """Extract release date in YYYY-MM-DD format"""
        if not game_info:
            return None
        # Implement date extraction and formatting
        pass

    def _extract_genres(self, game_info: dict) -> list[str] | None:
        """Extract genre names from game info"""
        if not game_info:
            return None
        # Implement genre extraction
        pass

    def _extract_game_modes(self, game_info: dict) -> list[str] | None:
        """Extract game mode names (Single player, Multiplayer, etc.)"""
        if not game_info:
            return None
        # Implement game mode extraction
        pass
```

### Step 2: Add Configuration

Add credentials to [consts.py](consts.py):

```python
# Add at the top with other imports
{STORE}_API_KEY = os.getenv('{STORE}_API_KEY')
{STORE}_USER_ID = os.getenv('{STORE}_USER_ID')
NOTION_STORE_{STORE}_ID = os.getenv('NOTION_STORE_{STORE}_ID')
```

Add to `.env` file:
```bash
{STORE}_API_KEY=your_api_key_here
{STORE}_USER_ID=your_user_id_here
NOTION_STORE_{STORE}_ID=notion_page_id_for_store
```

### Step 3: Register Integration

Update [main.py](main.py:77-83):

```python
def main():
    integrations = []

    if STEAM_API_KEY and STEAM_USERID_64:
        integrations.append(SteamIntegration(api_key=STEAM_API_KEY, steamid=STEAM_USERID_64))

    if GOG_PUBLIC_USERNAME:
        integrations.append(GogIntegration(username=GOG_PUBLIC_USERNAME))

    # Add your new integration
    if {STORE}_API_KEY and {STORE}_USER_ID:
        integrations.append({StoreName}Integration(
            api_key={STORE}_API_KEY,
            user_id={STORE}_USER_ID
        ))

    games = []
    for integration in integrations:
        owned_games = integration.get_owned_games()
        games.extend(owned_games)  # Now extends full objects, not just names

    if not games:
        print("No games found in any library.")
        return

    notion = NotionIntegration(NOTION_TOKEN)
    for game in games:
        write_game_optimized(notion, game)  # Use optimized version
```

### Step 4: Update Main Processor

Modify [main.py](main.py:62) to use optimized game writing:

```python
def write_game_optimized(notion, game_data, debug=False):
    """
    Write game to Notion, skipping IGDB calls if data already exists.

    Args:
        notion: NotionIntegration instance
        game_data: Normalized game dictionary from store integration
        debug: Enable debug output
    """
    title = game_data['name']
    print(f'--- Adding {title} ---')

    # Use store-provided data if available, otherwise call IGDB
    consoles = game_data.get('platforms')
    if consoles is None:
        consoles = handle_game_platforms(title, debug)
    else:
        # Convert from list of strings to list of dicts
        consoles = [{'name': platform} for platform in consoles]
        if debug:
            print(f"Using platforms from store: {', '.join(consoles)}")

    release_date = game_data.get('release_date')
    if release_date is None:
        release_date, failed = handle_game_release(title, debug)
    else:
        if debug:
            print(f"Using release date from store: {release_date}")

    genres = game_data.get('genres')
    if genres is None:
        genres = handle_game_genres(title, debug)
    else:
        # Convert from list of strings to list of dicts
        genres = [{'name': genre} for genre in genres]
        if debug:
            print(f"Using genres from store: {', '.join(genres)}")

    online = game_data.get('game_modes')
    if online is None:
        online = handle_game_modes(title)
    else:
        # Convert from list of strings to list of dicts
        online = [{'name': mode} for mode in online]
        if debug:
            print(f"Using game modes from store: {', '.join(online)}")

    cover = game_data.get('cover_url')
    if cover is None:
        cover = handle_game_cover(title)
    else:
        if debug:
            print(f"Using cover from store: {cover}")

    # HowLongToBeat is always needed (no store provides this)
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
    print('Game Added to Database')
```

---

## Optimizing Existing Integrations

### Steam Integration Enhancement

Update [steam_integration.py](steam_integration.py:37-47):

```python
def normalize_games_list(self, games):
    normalized_games = []
    for game in games:
        game_info = self.get_game_info(game['appid'])

        normalized_game = {
            'appid': game['appid'],
            'name': game['name'],
            'notion_store_id': NOTION_STORE_STEAM_ID,
        }

        # Add rich metadata from Steam API
        if game_info:
            # Extract platforms
            platforms = []
            if game_info.get('platforms', {}).get('windows'):
                platforms.append('PC (Microsoft Windows)')
            if game_info.get('platforms', {}).get('mac'):
                platforms.append('Mac')
            if game_info.get('platforms', {}).get('linux'):
                platforms.append('Linux')
            if platforms:
                normalized_game['platforms'] = platforms

            # Extract cover image
            if 'header_image' in game_info:
                normalized_game['cover_url'] = game_info['header_image']

            # Extract release date
            release_info = game_info.get('release_date', {})
            if not release_info.get('coming_soon', True) and 'date' in release_info:
                # Convert "Jan 1, 2020" to "2020-01-01"
                try:
                    from datetime import datetime
                    date_str = release_info['date']
                    date_obj = datetime.strptime(date_str, "%b %d, %Y")
                    normalized_game['release_date'] = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    pass  # Invalid date format

            # Extract genres
            if 'genres' in game_info:
                normalized_game['genres'] = [g['description'] for g in game_info['genres']]

            # Extract game modes
            categories = game_info.get('categories', [])
            game_modes = []
            for cat in categories:
                if cat['id'] == 1:  # Multi-player
                    game_modes.append('Multiplayer')
                elif cat['id'] == 2:  # Single-player
                    game_modes.append('Single player')
                elif cat['id'] == 9:  # Co-op
                    game_modes.append('Co-operative')
            if game_modes:
                normalized_game['game_modes'] = game_modes

        normalized_games.append(normalized_game)
    return normalized_games
```

### GOG Integration Enhancement

Update [gog_integration.py](gog_integration.py:80-89):

```python
def normalize_games_list(self, games):
    normalized_games = []
    for game in games:
        normalized_game = {
            'appid': game['id'],
            'name': game['title'],
            'notion_store_id': NOTION_STORE_GOG_ID,
        }

        # GOG is primarily PC-only
        normalized_game['platforms'] = ['PC (Microsoft Windows)']

        # Extract cover if available
        if 'image' in game:
            normalized_game['cover_url'] = game['image']

        # Try to get additional info from detailed endpoint
        game_info = self.get_game_info(game['id'])
        if game_info:
            # Extract platforms from worksOn
            if 'worksOn' in game_info:
                platforms = []
                if game_info['worksOn'].get('Windows'):
                    platforms.append('PC (Microsoft Windows)')
                if game_info['worksOn'].get('Mac'):
                    platforms.append('Mac')
                if game_info['worksOn'].get('Linux'):
                    platforms.append('Linux')
                normalized_game['platforms'] = platforms

            # GOG API may provide additional metadata
            if 'releaseDate' in game_info:
                # Convert timestamp to YYYY-MM-DD
                from datetime import datetime
                try:
                    timestamp = game_info['releaseDate']
                    date_obj = datetime.fromtimestamp(timestamp)
                    normalized_game['release_date'] = date_obj.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    pass

        normalized_games.append(normalized_game)
    return normalized_games
```

---

## Data Normalization Best Practices

### 1. Required Fields

Always include these fields:
```python
{
    'appid': int,              # Platform-specific ID (required)
    'name': str,               # Game title (required)
    'notion_store_id': str,    # Notion relation ID (required)
}
```

### 2. Optional Fields for Optimization

Include when available to skip IGDB API calls:

```python
{
    'platforms': list[str],    # ['PC (Microsoft Windows)', 'PlayStation 4']
    'cover_url': str,          # Direct URL to cover image
    'release_date': str,       # 'YYYY-MM-DD' format
    'genres': list[str],       # ['Action', 'Adventure', 'RPG']
    'game_modes': list[str],   # ['Single player', 'Multiplayer']
}
```

### 3. Data Format Standards

**Platforms**: Use IGDB naming conventions
```python
# Good
['PC (Microsoft Windows)', 'PlayStation 4', 'Xbox One', 'Nintendo Switch']

# Bad
['PC', 'PS4', 'XB1', 'Switch']
```

**Release Dates**: Always use ISO format
```python
# Good
'2020-03-20'

# Bad
'March 20, 2020'
'03/20/2020'
'20-03-2020'
```

**Game Modes**: Standard names
```python
# Common values
['Single player', 'Multiplayer', 'Co-operative', 'Split screen', 'Massively Multiplayer Online (MMO)']
```

**Genres**: Use IGDB genre names when possible
```python
# IGDB genres
['Action', 'Adventure', 'Fighting', 'Indie', 'Platform', 'Puzzle', 'Racing',
 'Role-playing (RPG)', 'Shooter', 'Simulator', 'Sport', 'Strategy']
```

### 4. Error Handling

Always handle missing/invalid data gracefully:

```python
def _extract_release_date(self, game_info: dict) -> str | None:
    """
    Extract release date with proper error handling.

    Returns:
        Date string in YYYY-MM-DD format or None
    """
    if not game_info or 'release_date' not in game_info:
        return None

    try:
        # Attempt to parse date
        date_str = game_info['release_date']
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%Y-%m-%d")
    except (ValueError, TypeError) as e:
        print(f"Warning: Invalid date format: {game_info.get('release_date')}")
        return None
```

### 5. Remove None Values

Clean up the normalized dictionary:

```python
# Remove None values to keep data clean
normalized_game = {k: v for k, v in normalized_game.items() if v is not None}
```

---

## Testing Your Integration

### Unit Tests

Create `tests/test_{store}_integration.py`:

```python
import unittest
from {store}_integration import {StoreName}Integration
from consts import {STORE}_API_KEY, {STORE}_USER_ID

class Test{StoreName}Integration(unittest.TestCase):
    def setUp(self):
        self.integration = {StoreName}Integration(
            api_key={STORE}_API_KEY,
            user_id={STORE}_USER_ID
        )

    def test_get_owned_games(self):
        """Test fetching owned games"""
        games = self.integration.get_owned_games()
        self.assertIsInstance(games, list)
        self.assertGreater(len(games), 0)

        # Check first game has required fields
        game = games[0]
        self.assertIn('appid', game)
        self.assertIn('name', game)
        self.assertIn('notion_store_id', game)

    def test_get_game_info(self):
        """Test fetching detailed game info"""
        # Use a known game ID
        game_info = self.integration.get_game_info(12345)
        self.assertIsNotNone(game_info)
        self.assertIsInstance(game_info, dict)

    def test_normalization_format(self):
        """Test normalized data format"""
        games = self.integration.get_owned_games()
        game = games[0]

        # Check required fields
        self.assertIsInstance(game['appid'], int)
        self.assertIsInstance(game['name'], str)
        self.assertIsInstance(game['notion_store_id'], str)

        # Check optional fields if present
        if 'platforms' in game:
            self.assertIsInstance(game['platforms'], list)
            self.assertGreater(len(game['platforms']), 0)

        if 'release_date' in game:
            self.assertRegex(game['release_date'], r'^\d{4}-\d{2}-\d{2}$')

        if 'genres' in game:
            self.assertIsInstance(game['genres'], list)

    def test_optimization_coverage(self):
        """Test how many games have optional fields (optimization coverage)"""
        games = self.integration.get_owned_games()

        with_platforms = sum(1 for g in games if 'platforms' in g)
        with_cover = sum(1 for g in games if 'cover_url' in g)
        with_release = sum(1 for g in games if 'release_date' in g)
        with_genres = sum(1 for g in games if 'genres' in g)

        total = len(games)
        print(f"\nOptimization Coverage:")
        print(f"  Platforms: {with_platforms}/{total} ({with_platforms/total*100:.1f}%)")
        print(f"  Cover URLs: {with_cover}/{total} ({with_cover/total*100:.1f}%)")
        print(f"  Release Dates: {with_release}/{total} ({with_release/total*100:.1f}%)")
        print(f"  Genres: {with_genres}/{total} ({with_genres/total*100:.1f}%)")

if __name__ == '__main__':
    unittest.main()
```

### Integration Tests

Test with actual Notion database:

```python
def test_end_to_end_integration():
    """Test complete flow from store to Notion"""
    # Get games from store
    integration = {StoreName}Integration(credentials)
    games = integration.get_owned_games()

    # Write first game to Notion
    notion = NotionIntegration(NOTION_TOKEN)
    test_game = games[0]
    write_game_optimized(notion, test_game, debug=True)

    # Verify game was added (would require Notion query)
    print(f"Successfully added: {test_game['name']}")
```

### Manual Testing

Run standalone test:

```python
# In {store}_integration.py
if __name__ == "__main__":
    integration = {StoreName}Integration(credentials)
    owned_games = integration.get_owned_games()

    print(f"Found {len(owned_games)} games")
    print("\nFirst 5 games:")
    for game in owned_games[:5]:
        print(f"\n{game['name']} (ID: {game['appid']})")
        print(f"  Store: {game['notion_store_id']}")

        if 'platforms' in game:
            print(f"  Platforms: {', '.join(game['platforms'])}")
        if 'cover_url' in game:
            print(f"  Cover: {game['cover_url'][:50]}...")
        if 'release_date' in game:
            print(f"  Released: {game['release_date']}")
        if 'genres' in game:
            print(f"  Genres: {', '.join(game['genres'])}")
```

---

## Examples: Popular Store APIs

### Epic Games Store

**API Documentation**: https://dev.epicgames.com/docs/web-api-ref

**Key Endpoints**:
- Get owned games: Requires OAuth authentication
- Game details: `/catalog/items/{item_id}`

**Implementation Notes**:
- Requires OAuth 2.0 flow
- Provides excellent metadata including platforms, genres, release dates
- Has high-quality cover images

**Optimization Potential**: ⭐⭐⭐⭐⭐ (Excellent)

### Xbox Live / Microsoft Store

**API Documentation**: https://docs.microsoft.com/en-us/gaming/xbox-live/

**Key Endpoints**:
- Get owned games: Xbox Live Social API
- Game details: Microsoft Store API

**Implementation Notes**:
- Requires Xbox Live authentication
- Provides comprehensive metadata
- Cover images available in multiple sizes

**Optimization Potential**: ⭐⭐⭐⭐ (Very Good)

### PlayStation Network

**API Documentation**: Unofficial (no official public API)

**Key Endpoints**:
- Various community APIs available
- Consider using PSNAPI or similar libraries

**Implementation Notes**:
- No official API, requires workarounds
- Limited metadata available
- May require web scraping

**Optimization Potential**: ⭐⭐ (Limited)

### Nintendo eShop

**API Documentation**: Unofficial

**Key Endpoints**:
- Nintendo eShop search API
- No official owned games API

**Implementation Notes**:
- No official API for owned games
- Would require scraping My Nintendo account
- Limited automation potential

**Optimization Potential**: ⭐ (Very Limited)

### Itch.io

**API Documentation**: https://itch.io/docs/api/overview

**Key Endpoints**:
- Get owned games: `/profile/owned-keys`
- Game details: `/games/{game_id}`

**Implementation Notes**:
- Simple API key authentication
- Good metadata coverage
- Free and easy to implement

**Optimization Potential**: ⭐⭐⭐⭐ (Very Good)

---

## Optimization Impact Analysis

### Before Optimization

For each game:
1. Store API: Get game name (1 call per game)
2. IGDB API: Get game ID (1 call per game)
3. IGDB API: Get platforms (1 call per game)
4. IGDB API: Get release date (1 call per game)
5. IGDB API: Get genres (2 calls per game - genres + themes)
6. IGDB API: Get game modes (1 call per game)
7. IGDB API: Get cover (1 call per game)
8. HowLongToBeat API: Get completion time (1 call per game)

**Total: 9 external API calls per game**

### After Optimization (Steam Example)

For each game:
1. Store API: Get all metadata (1-2 calls per game)
   - Provides: name, platforms, cover, release date, genres
2. ~~IGDB API: Get game ID~~ ❌ Skipped
3. ~~IGDB API: Get platforms~~ ❌ Skipped
4. ~~IGDB API: Get release date~~ ❌ Skipped
5. ~~IGDB API: Get genres~~ ❌ Skipped
6. IGDB API: Get game modes (1 call per game) - Steam doesn't provide this
7. ~~IGDB API: Get cover~~ ❌ Skipped
8. HowLongToBeat API: Get completion time (1 call per game)

**Total: 3-4 external API calls per game**

**Performance Improvement**: ~55-60% reduction in API calls

### Rate Limit Comparison

**API Rate Limits**:
- **Steam Web API**: 100,000 calls/day (~1.16 calls/second) - [Official Terms](https://steamcommunity.com/dev/apiterms)
- **IGDB API**: 4 requests/second

**Processing 100 games**:

| Scenario | Total API Calls | Time (minimum) |
|----------|----------------|----------------|
| Before Optimization | 900 calls | 225 seconds (~4 minutes) |
| After Optimization | 400 calls | 100 seconds (~1.5 minutes) |
| **Savings** | **500 calls** | **~2.5 minutes** |

For larger libraries (1000+ games), the time savings become even more significant.

---

## Troubleshooting

### Issue: Store API doesn't provide certain metadata

**Solution**: Only populate fields that are available. The system will fall back to IGDB for missing data.

```python
# Good approach
if 'platforms' in game_info:
    normalized_game['platforms'] = self._extract_platforms(game_info)
# If not available, don't set it - IGDB will be used
```

### Issue: Date format conversion errors

**Solution**: Use try-except with clear error messages

```python
def _parse_date(self, date_str: str) -> str | None:
    """Try multiple date formats"""
    formats = [
        "%Y-%m-%d",
        "%b %d, %Y",
        "%m/%d/%Y",
        "%d/%m/%Y"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    print(f"Warning: Could not parse date: {date_str}")
    return None
```

### Issue: Integration returns too many API errors

**Solution**: Implement retry logic with exponential backoff

```python
import time

def _api_call_with_retry(self, url: str, max_retries: int = 3) -> dict | None:
    """Make API call with retry logic"""
    for attempt in range(max_retries):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    return None
```

---

## Best Practices Checklist

Before submitting your integration:

- [ ] Implements `StoreIntegrationProtocol`
- [ ] Handles API authentication securely
- [ ] Normalizes data to standard format
- [ ] Extracts all available metadata (platforms, cover, dates, genres)
- [ ] Includes error handling for API failures
- [ ] Removes `None` values from normalized output
- [ ] Formats dates as YYYY-MM-DD
- [ ] Uses IGDB-compatible platform names
- [ ] Includes unit tests
- [ ] Documents any limitations or special requirements
- [ ] Adds configuration to [consts.py](consts.py)
- [ ] Updates [main.py](main.py) to register integration
- [ ] Tests end-to-end with actual Notion database

---

## Next Steps

1. Choose a store to integrate
2. Research their API documentation
3. Create integration file using template above
4. Test with a small subset of games
5. Measure optimization impact
6. Submit pull request (if contributing to project)

For questions or issues, refer to:
- [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- [API_REFERENCE.md](API_REFERENCE.md) for detailed API documentation
- [README.md](README.md) for setup instructions
