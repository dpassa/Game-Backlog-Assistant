# Game Status Sync Feature

## Overview

The Game Status Sync feature automatically updates your Notion game database with achievement completion percentages and dynamic status based on your play history from Steam and other stores.

**Important**: As of the latest version, status sync is **fully integrated into `main.py`**. You no longer need to run a separate sync script for most use cases.

## Features

### Automatic Status Updates

The system automatically assigns one of five statuses to each game based on achievement completion and last played date:

| Status | Condition |
|--------|-----------|
| **Complete** | All achievements are 100% completed |
| **Currently Playing** | Last game session was within 1 month |
| **Backlog** | Never played (no recorded play session) |
| **On Hold** | Last game session was between 1 month and 2 years ago |
| **Abandoned** | Last game session was more than 2 years ago |

### Achievement Tracking

- Fetches achievement completion percentage from Steam
- Updates the `Achievements` field in Notion with percentage (0-100)
- Uses Steam API to check total achievements vs. unlocked achievements

## How It Works

### Unified Workflow (Integrated in main.py)

When you run `python main.py`, the system automatically:

1. **Fetches games from your stores** (Steam, GOG)
2. **For each game**:
   - If game **doesn't exist** in Notion:
     - Fetches metadata
     - Gets achievement data
     - Calculates initial status
     - **Creates entry with accurate status and achievements**
   - If game **exists** in Notion:
     - Fetches achievement data
     - Calculates current status
     - **Updates status and achievements**

This unified approach means:
- ✅ New games get accurate initial status (not just "Backlog")
- ✅ Existing games automatically updated
- ✅ Single command does everything

## Usage

### Recommended: Unified Sync

```bash
python main.py
```

This will add new games AND update existing games with current status and achievements.

### With Debug Output

```bash
python main.py --debug
```

### Standalone Status Sync (Optional)

A standalone script is available if you **only** want to update statuses without checking for new games:

```bash
python sync_status.py
```

**When to use sync_status.py:**
- Quick status refresh without full library scan
- After playing games (just update achievements)
- Testing status updates without adding games

**Note**: Most users should use `python main.py` as it handles both adding and updating efficiently.

### Example Output (main.py)

```
Fetching games from 1 store(s)...
  Loading Steam library...
  Found 150 games in Steam

Total games to process: 150
🚀 Processing games (unified add/update mode)

[1/150] --- Adding The Witcher 3: Wild Hunt ---
📊 Initial Achievements: 67.5%
🎯 Initial Status: On Hold
✓ Game Added to Database

[2/150] --- Updating Hades ---
📊 Achievements: 100%
🎯 Status: Complete
✓ Game Updated: Updated game with status: Complete, achievements: 100%

[3/150] --- Adding Cyberpunk 2077 ---
📊 Initial Achievements: 15%
🎯 Initial Status: Currently Playing
✓ Game Added to Database

============================================================
✓ Sync completed!
============================================================
Added: 50 | Updated: 75 | Skipped: 20 | Errors: 5
```

## Performance Considerations

### Caching

The Steam integration uses smart caching to minimize API calls:
- Achievement data is cached for 24 hours by default
- Recently played data is cached
- Game details are cached

### Rate Limiting

- Respects Steam API rate limits (100,000 calls/day)
- Uses adaptive rate limiting to prevent 429 errors
- Only fetches data for games that are not already complete

### Optimization Tips

1. **Use unified workflow**: Just run `python main.py` for both new games and updates
2. **Run periodically**: Set up a scheduled task to run weekly or monthly
3. **Leverage caching**: Subsequent runs are much faster due to 24-hour cache

## API Requirements

### Steam

Required environment variables:
- `STEAM_API_KEY`: Your Steam Web API key
- `STEAM_USERID_64`: Your Steam 64-bit user ID

### GOG

GOG achievement tracking is not yet implemented. The system will skip GOG games during status sync.

## Status Calculation Logic

### Complete Status
```python
if achievement_percentage == 100:
    return "Complete"
```

### Backlog Status
```python
if last_played_date is None:
    return "Backlog"
```

### Currently Playing Status
```python
if time_since_played <= 30 days:
    return "Currently Playing"
```

### On Hold Status
```python
if 30 days < time_since_played <= 365 days:
    return "On Hold"
```

### Abandoned Status
```python
if time_since_played > 730 days:
    return "Abandoned"
```

## Benefits of Integrated Sync

✅ **Single unified command** - No need to run multiple scripts
✅ **New games get accurate initial status** - No default "Backlog" for completed games
✅ **Existing games automatically updated** - Status and achievements stay current
✅ **Fewer API calls** - Reuses integration data efficiently
✅ **Better user experience** - One command does everything

## Notion Database Requirements

Your Notion database must have these properties:
- `title`: Game title (title property)
- `External ID`: Rich text field for store ID
- `Store Name`: Rich text field for store name
- `Store`: Relation to store pages
- `Status`: Select property with these options:
  - Currently Playing
  - Backlog
  - Complete
  - On Hold
  - Abandoned
- `Achievements`: Number property for achievement percentage

## Troubleshooting

### No games being updated

**Check:**
- Ensure games have valid `External ID` values
- Verify `Store Name` matches exactly ("Steam", "GOG")
- Confirm Steam API credentials are set correctly

### Achievement data not fetching

**Check:**
- Steam profile must be public
- Game must have achievements (not all games do)
- Verify Steam API key is valid and not rate limited

### Status not changing

**Check:**
- Current status in Notion
- Last played date from Steam
- Achievement completion percentage
- Review status calculation logic above

## Future Enhancements

Potential improvements for future versions:
- GOG achievement tracking support
- PlayStation Network integration
- Xbox Live achievement tracking
- Manual override options
- Customizable status thresholds
- Playtime-based status updates

## Code Structure

### Main Components

1. **main.py**: Unified orchestration script (handles both add and update)
2. **notion_integration.py**:
   - `get_all_games()`: Retrieve games from Notion
   - `update_game_status_and_achievements()`: Update game properties
   - `write_row()`: Create new game with initial status and achievements
3. **steam_integration.py**:
   - `get_player_achievements()`: Fetch achievement data
   - `get_recently_played_games()`: Get last played info
   - `calculate_status()`: Determine appropriate status
   - `get_enriched_game_data()`: Combine all data sources
4. **sync_status.py**: Standalone script for status-only updates (optional)

### Data Flow

```
main.py → Fetch all games from stores
    ↓
For each game:
    ↓
    ├── Game exists in Notion?
    │   ├── YES → get_enriched_game_data() → update_game_status_and_achievements()
    │   └── NO → get_enriched_game_data() → write_row() (with initial status)
    ↓
Print statistics (Added/Updated/Skipped)
```

## Best Practices

1. **Use unified workflow**: Just run `python main.py` for both new games and updates
2. **Schedule regular syncs**: Weekly or monthly to keep data fresh
3. **Monitor API usage**: Check Steam API usage to stay within limits
4. **Review logs**: Check for errors or games that couldn't be updated

## Related Files

- [main.py](../main.py) - Unified sync script
- [notion_integration.py](../notion_integration.py) - Notion API interface
- [steam_integration.py](../steam_integration.py) - Steam API integration
- [sync_status.py](../sync_status.py) - Standalone sync script (optional)
- [store_integration_protocol.py](../store_integration_protocol.py) - Data structures
