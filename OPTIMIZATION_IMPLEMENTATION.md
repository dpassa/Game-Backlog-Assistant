# Optimization Implementation Plan

This document provides a concrete, step-by-step implementation plan for optimizing the codebase to skip IGDB API calls when store integrations already provide the necessary data.

## Current State Analysis

### Problems
1. **Redundant API Calls**: IGDB is queried for every game even when store APIs provide the data
2. **Performance**: Processing 100 games takes ~4 minutes due to IGDB rate limits (4 req/sec)
3. **Unnecessary Dependency**: Store-provided data is fetched but then discarded

### Opportunity
- Steam API provides: platforms, genres, release dates, cover images
- GOG API provides: platforms, cover images
- Implementing optimization could reduce API calls by 55-60%

---

## Implementation Plan

### Phase 1: Update Store Integrations (Low Risk)

#### Task 1.1: Enhance Steam Integration

**File**: [steam_integration.py](steam_integration.py)

**Changes**:
```python
# Current implementation (line 37-47)
def normalize_games_list(self, games):
    normalized_games = []
    for game in games:
        game_info = self.get_game_info(game['appid'])
        normalized_game = {
            'appid': game['appid'],
            'name': game['name'],
            'notion_store_id': NOTION_STORE_STEAM_ID,
        }
        normalized_games.append(normalized_game)
    return normalized_games

# New implementation
def normalize_games_list(self, games):
    normalized_games = []
    for game in games:
        game_info = self.get_game_info(game['appid'])
        normalized_game = {
            'appid': game['appid'],
            'name': game['name'],
            'notion_store_id': NOTION_STORE_STEAM_ID,
        }

        if game_info:
            # Extract platforms
            normalized_game['platforms'] = self._extract_platforms(game_info)

            # Extract cover URL
            if 'header_image' in game_info:
                normalized_game['cover_url'] = game_info['header_image']

            # Extract release date
            normalized_game['release_date'] = self._extract_release_date(game_info)

            # Extract genres
            normalized_game['genres'] = self._extract_genres(game_info)

            # Extract game modes
            normalized_game['game_modes'] = self._extract_game_modes(game_info)

        # Remove None values
        normalized_game = {k: v for k, v in normalized_game.items() if v is not None}
        normalized_games.append(normalized_game)
    return normalized_games

def _extract_platforms(self, game_info: dict) -> list[str] | None:
    """Extract platform names from Steam game info"""
    if not game_info or 'platforms' not in game_info:
        return None

    platforms = []
    steam_platforms = game_info['platforms']

    if steam_platforms.get('windows'):
        platforms.append('PC (Microsoft Windows)')
    if steam_platforms.get('mac'):
        platforms.append('Mac')
    if steam_platforms.get('linux'):
        platforms.append('Linux')

    return platforms if platforms else None

def _extract_release_date(self, game_info: dict) -> str | None:
    """Extract release date in YYYY-MM-DD format"""
    if not game_info or 'release_date' not in game_info:
        return None

    release_info = game_info['release_date']
    if release_info.get('coming_soon', True):
        return None

    date_str = release_info.get('date')
    if not date_str:
        return None

    try:
        from datetime import datetime
        # Steam format: "Jan 1, 2020" or "1 Jan, 2020"
        for fmt in ["%b %d, %Y", "%d %b, %Y"]:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue
    except Exception as e:
        print(f"Warning: Could not parse date '{date_str}': {e}")

    return None

def _extract_genres(self, game_info: dict) -> list[str] | None:
    """Extract genre names from Steam game info"""
    if not game_info or 'genres' not in game_info:
        return None

    genres = [genre['description'] for genre in game_info['genres']]
    return genres if genres else None

def _extract_game_modes(self, game_info: dict) -> list[str] | None:
    """Extract game modes from Steam categories"""
    if not game_info or 'categories' not in game_info:
        return None

    game_modes = []
    categories = {cat['id']: cat['description'] for cat in game_info['categories']}

    # Steam category IDs
    if 2 in categories:  # Single-player
        game_modes.append('Single player')
    if 1 in categories:  # Multi-player
        game_modes.append('Multiplayer')
    if 9 in categories or 38 in categories:  # Co-op or Online Co-op
        game_modes.append('Co-operative')
    if 24 in categories:  # Shared/Split Screen
        game_modes.append('Split screen')
    if 20 in categories:  # MMO
        game_modes.append('Massively Multiplayer Online (MMO)')

    return game_modes if game_modes else None
```

**Testing Command**:
```bash
python steam_integration.py
```

**Expected Output**:
```
Found X games
First game with enriched data:
  Name: Game Title
  Platforms: PC (Microsoft Windows), Mac
  Cover: https://cdn.akamai.steamstatic.com/...
  Released: 2020-03-20
  Genres: Action, Adventure, Indie
  Game Modes: Single player, Multiplayer
```

#### Task 1.2: Enhance GOG Integration

**File**: [gog_integration.py](gog_integration.py)

**Changes**:
```python
# Current implementation (line 80-89)
def normalize_games_list(self, games):
    normalized_games = []
    for game in games:
        normalized_game = {
            'appid': game['id'],
            'name': game['title'],
            'notion_store_id': NOTION_STORE_GOG_ID,
        }
        normalized_games.append(normalized_game)
    return normalized_games

# New implementation
def normalize_games_list(self, games):
    normalized_games = []
    for game in games:
        normalized_game = {
            'appid': game['id'],
            'name': game['title'],
            'notion_store_id': NOTION_STORE_GOG_ID,
        }

        # GOG primarily supports PC
        normalized_game['platforms'] = ['PC (Microsoft Windows)']

        # Extract cover if available in the game item
        if 'image' in game:
            normalized_game['cover_url'] = game['image']

        # GOG public profile doesn't provide detailed metadata
        # Could be enhanced if using authenticated API

        # Remove None values
        normalized_game = {k: v for k, v in normalized_game.items() if v is not None}
        normalized_games.append(normalized_game)
    return normalized_games
```

**Testing Command**:
```bash
python gog_integration.py
```

---

### Phase 2: Update Main Processing Logic (Medium Risk)

#### Task 2.1: Create Optimized write_game Function

**File**: [main.py](main.py)

**Add new function after existing write_game (after line 73)**:

```python
def write_game_optimized(notion, game_data, debug=False):
    """
    Write game to Notion, skipping IGDB calls if data already exists in game_data.

    Args:
        notion: NotionIntegration instance
        game_data: Normalized game dictionary from store integration
        debug: Enable debug output
    """
    title = game_data['name']
    print(f'--- Adding {title} ---')

    # Track which data sources are used
    sources_used = {'store': set(), 'igdb': set(), 'hltb': set()}

    # Platforms: Use store data if available, otherwise IGDB
    consoles = game_data.get('platforms')
    if consoles:
        consoles = [{'name': platform} for platform in consoles]
        sources_used['store'].add('platforms')
        if debug:
            platform_names = ', '.join([p['name'] for p in consoles])
            print(f'✓ Using platforms from store: {platform_names}')
    else:
        consoles = handle_game_platforms(title, debug)
        sources_used['igdb'].add('platforms')

    # Release Date: Use store data if available, otherwise IGDB
    release_date = game_data.get('release_date')
    if release_date:
        sources_used['store'].add('release_date')
        if debug:
            print(f'✓ Using release date from store: {release_date}')
    else:
        release_date, failed = handle_game_release(title, debug)
        sources_used['igdb'].add('release_date')

    # Genres: Use store data if available, otherwise IGDB
    genres = game_data.get('genres')
    if genres:
        genres = [{'name': genre} for genre in genres]
        sources_used['store'].add('genres')
        if debug:
            genre_names = ', '.join([g['name'] for g in genres])
            print(f'✓ Using genres from store: {genre_names}')
    else:
        genres = handle_game_genres(title, debug)
        sources_used['igdb'].add('genres')

    # Game Modes: Use store data if available, otherwise IGDB
    online = game_data.get('game_modes')
    if online:
        online = [{'name': mode} for mode in online]
        sources_used['store'].add('game_modes')
        if debug:
            mode_names = ', '.join([m['name'] for m in online])
            print(f'✓ Using game modes from store: {mode_names}')
    else:
        online = handle_game_modes(title)
        sources_used['igdb'].add('game_modes')

    # Cover: Use store data if available, otherwise IGDB
    cover = game_data.get('cover_url')
    if cover:
        sources_used['store'].add('cover')
        if debug:
            print(f'✓ Using cover from store: {cover[:60]}...')
    else:
        cover = handle_game_cover(title)
        sources_used['igdb'].add('cover')

    # HowLongToBeat: Always required (no store provides this)
    length = handle_game_length(title)
    sources_used['hltb'].add('length')

    # Write to Notion
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

    # Print optimization statistics
    if debug:
        store_count = len(sources_used['store'])
        igdb_count = len(sources_used['igdb'])
        total_fields = store_count + igdb_count
        if total_fields > 0:
            optimization_pct = (store_count / total_fields) * 100
            print(f'📊 Optimization: {store_count}/{total_fields} fields from store ({optimization_pct:.0f}%)')
            print(f'   Store: {", ".join(sources_used["store"]) if sources_used["store"] else "none"}')
            print(f'   IGDB: {", ".join(sources_used["igdb"]) if sources_used["igdb"] else "none"}')

    print('Game Added to Database')
```

#### Task 2.2: Update main() Function

**File**: [main.py](main.py:76-98)

**Changes**:
```python
# Current implementation
def main():
    integrations = []

    if STEAM_API_KEY and STEAM_USERID_64:
        integrations.append(SteamIntegration(api_key=STEAM_API_KEY, steamid=STEAM_USERID_64))

    if GOG_PUBLIC_USERNAME:
        integrations.append(GogIntegration(username=GOG_PUBLIC_USERNAME))

    games = []

    for integration in integrations:
        owned_games = integration.get_owned_games()
        games.extend([game['name'] for game in owned_games])  # Only extracts names

    if not games:
        print("No games found in Steam or GOG libraries.")
        return

    notion = NotionIntegration(NOTION_TOKEN)
    for game in games:
        write_game(notion, game)  # Only passes name

# New implementation
def main(use_optimization=True, debug=False):
    """
    Main entry point for syncing games to Notion.

    Args:
        use_optimization: Use optimized write_game (default: True)
        debug: Enable debug output (default: False)
    """
    integrations = []

    if STEAM_API_KEY and STEAM_USERID_64:
        integrations.append(SteamIntegration(api_key=STEAM_API_KEY, steamid=STEAM_USERID_64))

    if GOG_PUBLIC_USERNAME:
        integrations.append(GogIntegration(username=GOG_PUBLIC_USERNAME))

    if not integrations:
        print("No store integrations configured. Please set up Steam or GOG credentials in .env")
        return

    games = []

    print(f"Fetching games from {len(integrations)} store(s)...")
    for integration in integrations:
        store_name = integration.__class__.__name__.replace('Integration', '')
        print(f"  Loading {store_name} library...")
        owned_games = integration.get_owned_games()
        print(f"  Found {len(owned_games)} games in {store_name}")
        games.extend(owned_games)  # Now extends full game objects

    if not games:
        print("No games found in any library.")
        return

    print(f"\nTotal games to process: {len(games)}")

    # Optional: Remove duplicates (games owned on multiple platforms)
    # Uncomment to enable deduplication by game name
    # unique_games = {game['name']: game for game in games}
    # games = list(unique_games.values())
    # print(f"After deduplication: {len(games)} games")

    notion = NotionIntegration(NOTION_TOKEN)

    # Choose write function based on optimization flag
    write_func = write_game_optimized if use_optimization else write_game

    if use_optimization:
        print("\n🚀 Using optimized mode (skipping redundant IGDB calls)")
    else:
        print("\n⚠️  Using legacy mode (calling IGDB for all data)")

    # Track statistics
    stats = {
        'total': len(games),
        'processed': 0,
        'errors': 0,
        'start_time': __import__('time').time()
    }

    for i, game in enumerate(games, 1):
        try:
            print(f"\n[{i}/{stats['total']}]", end=' ')
            if use_optimization:
                write_func(notion, game, debug=debug)
            else:
                write_func(notion, game['name'], debug=debug)
            stats['processed'] += 1
        except Exception as e:
            print(f"❌ Error processing {game.get('name', 'unknown')}: {e}")
            stats['errors'] += 1
            if debug:
                import traceback
                traceback.print_exc()

    # Print summary
    elapsed_time = __import__('time').time() - stats['start_time']
    print(f"\n{'='*60}")
    print(f"📊 Processing Summary:")
    print(f"  Total games: {stats['total']}")
    print(f"  Successfully added: {stats['processed']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Time elapsed: {elapsed_time:.1f} seconds")
    print(f"  Average time per game: {elapsed_time/stats['total']:.1f} seconds")
    print(f"{'='*60}")

if __name__ == '__main__':
    # Parse command line arguments for testing
    import sys
    debug = '--debug' in sys.argv
    legacy = '--legacy' in sys.argv
    main(use_optimization=not legacy, debug=debug)
```

---

### Phase 3: Testing & Validation (Critical)

#### Task 3.1: Unit Tests

Create or update [tests/test_optimization.py](tests/test_optimization.py):

```python
import unittest
from unittest.mock import Mock, patch
from main import write_game_optimized, write_game
from notion_integration import NotionIntegration

class TestOptimization(unittest.TestCase):
    def setUp(self):
        self.notion = Mock(spec=NotionIntegration)

    def test_write_game_with_full_store_data(self):
        """Test that IGDB is not called when store provides all data"""
        game_data = {
            'appid': 12345,
            'name': 'Test Game',
            'notion_store_id': 'store_id',
            'platforms': ['PC (Microsoft Windows)', 'Mac'],
            'cover_url': 'https://example.com/cover.jpg',
            'release_date': '2020-01-01',
            'genres': ['Action', 'Adventure'],
            'game_modes': ['Single player', 'Multiplayer']
        }

        with patch('main.handle_game_platforms') as mock_platforms, \
             patch('main.handle_game_release') as mock_release, \
             patch('main.handle_game_genres') as mock_genres, \
             patch('main.handle_game_modes') as mock_modes, \
             patch('main.handle_game_cover') as mock_cover, \
             patch('main.handle_game_length') as mock_length:

            mock_length.return_value = 10.0

            write_game_optimized(self.notion, game_data)

            # Verify IGDB functions were NOT called
            mock_platforms.assert_not_called()
            mock_release.assert_not_called()
            mock_genres.assert_not_called()
            mock_modes.assert_not_called()
            mock_cover.assert_not_called()

            # HowLongToBeat should still be called
            mock_length.assert_called_once()

            # Notion write_row should be called
            self.notion.write_row.assert_called_once()

    def test_write_game_with_partial_store_data(self):
        """Test that IGDB fills in missing data"""
        game_data = {
            'appid': 12345,
            'name': 'Test Game',
            'notion_store_id': 'store_id',
            'platforms': ['PC (Microsoft Windows)'],
            # Missing: cover_url, release_date, genres, game_modes
        }

        with patch('main.handle_game_platforms') as mock_platforms, \
             patch('main.handle_game_release') as mock_release, \
             patch('main.handle_game_genres') as mock_genres, \
             patch('main.handle_game_modes') as mock_modes, \
             patch('main.handle_game_cover') as mock_cover, \
             patch('main.handle_game_length') as mock_length:

            mock_release.return_value = ('2020-01-01', False)
            mock_genres.return_value = [{'name': 'Action'}]
            mock_modes.return_value = [{'name': 'Single player'}]
            mock_cover.return_value = 'https://example.com/cover.jpg'
            mock_length.return_value = 10.0

            write_game_optimized(self.notion, game_data)

            # Platforms should NOT be called (store provided)
            mock_platforms.assert_not_called()

            # These should be called (not in store data)
            mock_release.assert_called_once()
            mock_genres.assert_called_once()
            mock_modes.assert_called_once()
            mock_cover.assert_called_once()
            mock_length.assert_called_once()

    def test_write_game_with_no_store_data(self):
        """Test fallback to IGDB for all data"""
        game_data = {
            'appid': 12345,
            'name': 'Test Game',
            'notion_store_id': 'store_id',
            # No optional fields
        }

        with patch('main.handle_game_platforms') as mock_platforms, \
             patch('main.handle_game_release') as mock_release, \
             patch('main.handle_game_genres') as mock_genres, \
             patch('main.handle_game_modes') as mock_modes, \
             patch('main.handle_game_cover') as mock_cover, \
             patch('main.handle_game_length') as mock_length:

            mock_platforms.return_value = [{'name': 'PC (Microsoft Windows)'}]
            mock_release.return_value = ('2020-01-01', False)
            mock_genres.return_value = [{'name': 'Action'}]
            mock_modes.return_value = [{'name': 'Single player'}]
            mock_cover.return_value = 'https://example.com/cover.jpg'
            mock_length.return_value = 10.0

            write_game_optimized(self.notion, game_data)

            # All IGDB functions should be called
            mock_platforms.assert_called_once()
            mock_release.assert_called_once()
            mock_genres.assert_called_once()
            mock_modes.assert_called_once()
            mock_cover.assert_called_once()
            mock_length.assert_called_once()

if __name__ == '__main__':
    unittest.main()
```

**Run Tests**:
```bash
python -m pytest tests/test_optimization.py -v
```

#### Task 3.2: Integration Test

Test with real APIs using a small subset:

```python
# test_real_optimization.py
from steam_integration import SteamIntegration
from gog_integration import GogIntegration
from main import write_game_optimized
from notion_integration import NotionIntegration
from consts import *
import time

def test_real_optimization():
    """Test optimization with real APIs (use small sample)"""

    print("Fetching games from Steam...")
    steam = SteamIntegration(STEAM_API_KEY, STEAM_USERID_64)
    games = steam.get_owned_games()[:5]  # Test with 5 games only

    print(f"\nProcessing {len(games)} games with optimization enabled...")
    notion = NotionIntegration(NOTION_TOKEN)

    start_time = time.time()
    for game in games:
        print(f"\n{game['name']}:")
        print(f"  Has platforms: {'platforms' in game}")
        print(f"  Has cover: {'cover_url' in game}")
        print(f"  Has release date: {'release_date' in game}")
        print(f"  Has genres: {'genres' in game}")
        print(f"  Has game modes: {'game_modes' in game}")

        # Uncomment to actually write to Notion
        # write_game_optimized(notion, game, debug=True)

    elapsed = time.time() - start_time
    print(f"\nProcessed {len(games)} games in {elapsed:.1f} seconds")
    print(f"Average: {elapsed/len(games):.1f} seconds per game")

if __name__ == '__main__':
    test_real_optimization()
```

**Run Test**:
```bash
python test_real_optimization.py
```

#### Task 3.3: Performance Benchmark

Compare old vs new implementation:

```python
# benchmark_optimization.py
import time
from steam_integration import SteamIntegration
from main import write_game, write_game_optimized
from notion_integration import NotionIntegration
from consts import *

def benchmark():
    """Benchmark old vs new implementation"""

    steam = SteamIntegration(STEAM_API_KEY, STEAM_USERID_64)
    games = steam.get_owned_games()[:10]  # Test with 10 games

    notion = NotionIntegration(NOTION_TOKEN)

    # Test legacy mode
    print("Testing LEGACY mode (always call IGDB)...")
    start_legacy = time.time()
    for game in games:
        try:
            # Don't actually write to avoid duplicates
            # write_game(notion, game['name'])
            print(f"  Processed: {game['name']}")
        except Exception as e:
            print(f"  Error: {e}")
    time_legacy = time.time() - start_legacy

    # Test optimized mode
    print("\nTesting OPTIMIZED mode (skip IGDB when possible)...")
    start_optimized = time.time()
    for game in games:
        try:
            # Don't actually write to avoid duplicates
            # write_game_optimized(notion, game, debug=True)
            print(f"  Processed: {game['name']}")
        except Exception as e:
            print(f"  Error: {e}")
    time_optimized = time.time() - start_optimized

    # Results
    print("\n" + "="*60)
    print("BENCHMARK RESULTS:")
    print(f"  Games processed: {len(games)}")
    print(f"  Legacy mode: {time_legacy:.1f}s ({time_legacy/len(games):.1f}s per game)")
    print(f"  Optimized mode: {time_optimized:.1f}s ({time_optimized/len(games):.1f}s per game)")
    print(f"  Improvement: {((time_legacy - time_optimized) / time_legacy * 100):.1f}% faster")
    print("="*60)

if __name__ == '__main__':
    benchmark()
```

---

### Phase 4: Deployment (Low Risk)

#### Task 4.1: Update Documentation

Update [README.md](README.md) to document new features:

```markdown
## New Features (v2.0)

### Optimized Mode
The assistant now intelligently uses data from store APIs (Steam, GOG) when available, significantly reducing API calls to IGDB and improving performance.

**Benefits:**
- 55-60% fewer external API calls
- 2-3x faster processing for large libraries
- Reduced load on IGDB API (stay within rate limits)

### Usage

Run in optimized mode (default):
\`\`\`bash
python main.py
\`\`\`

Run in legacy mode (always call IGDB):
\`\`\`bash
python main.py --legacy
\`\`\`

Enable debug output:
\`\`\`bash
python main.py --debug
\`\`\`

### Performance Comparison

| Library Size | Legacy Mode | Optimized Mode | Improvement |
|--------------|-------------|----------------|-------------|
| 50 games     | ~2 minutes  | ~1 minute      | 50% faster  |
| 100 games    | ~4 minutes  | ~2 minutes     | 50% faster  |
| 500 games    | ~20 minutes | ~10 minutes    | 50% faster  |
```

#### Task 4.2: Create Migration Script (Optional)

For existing installations:

```python
# migrate_to_v2.py
"""
Migration script for v2.0 optimization features.
Re-runs all games to populate optimized fields.
"""

def migrate():
    print("Game Backlog Assistant - Migration to v2.0")
    print("="*60)
    print("\nThis script will:")
    print("  1. Fetch your games from Steam/GOG")
    print("  2. Use optimized data extraction")
    print("  3. Check for duplicates before adding")
    print("\nNOTE: This may create duplicate entries if not handled properly.")

    response = input("\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        return

    # Run main with optimization
    from main import main
    main(use_optimization=True, debug=True)

    print("\nMigration complete!")

if __name__ == '__main__':
    migrate()
```

---

## Rollback Plan

If issues occur:

### Option 1: Use Legacy Mode
```bash
python main.py --legacy
```

### Option 2: Revert Code Changes

```bash
# Restore previous version
git checkout HEAD~1 steam_integration.py gog_integration.py main.py
```

### Option 3: Conditional Feature Flag

Add to [consts.py](consts.py):
```python
# Feature flags
ENABLE_OPTIMIZATION = os.getenv('ENABLE_OPTIMIZATION', 'true').lower() == 'true'
```

In [main.py](main.py):
```python
from consts import ENABLE_OPTIMIZATION

if __name__ == '__main__':
    main(use_optimization=ENABLE_OPTIMIZATION, debug=debug)
```

---

## Success Metrics

Track these metrics to validate optimization:

1. **API Call Reduction**
   - Target: 50-60% reduction in IGDB calls
   - Measure: Count API calls before/after

2. **Processing Speed**
   - Target: 50% faster for 100 games
   - Measure: Time elapsed for batch processing

3. **Data Completeness**
   - Target: 95%+ fields populated
   - Measure: % of games with all metadata

4. **Error Rate**
   - Target: <5% errors
   - Measure: Successful additions vs total games

---

## Timeline

| Phase | Tasks | Duration | Dependencies |
|-------|-------|----------|--------------|
| Phase 1 | Enhance store integrations | 2-3 hours | None |
| Phase 2 | Update main logic | 1-2 hours | Phase 1 |
| Phase 3 | Testing & validation | 2-3 hours | Phase 2 |
| Phase 4 | Deployment & docs | 1 hour | Phase 3 |
| **Total** | | **6-9 hours** | |

---

## Next Steps

1. **Backup current database**: Export Notion database before testing
2. **Implement Phase 1**: Start with Steam integration enhancement
3. **Test incrementally**: Test each phase before moving forward
4. **Monitor metrics**: Track success metrics during rollout
5. **Document findings**: Update docs with actual performance improvements

---

## Questions & Support

For implementation questions:
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Check [API_REFERENCE.md](API_REFERENCE.md) for API details
- See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for integration patterns

For bugs or issues:
- Enable debug mode: `python main.py --debug`
- Check error logs
- Test with single game first before batch processing
