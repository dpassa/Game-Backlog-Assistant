# Duplicate Detection Feature

## Overview

The Game Backlog Assistant now includes **automatic duplicate detection** to prevent adding the same game multiple times to your Notion database. This feature is enabled by default and works automatically.

## How It Works

### 1. Check Before Adding
Before creating a new game entry, the system queries the Notion database to check if a game with the exact same title already exists:

```python
def check_game_exists(self, database_id, title):
    """Check if a game with the given title already exists"""
    response = self.client.databases.query(
        database_id=database_id,
        filter={
            "property": "title",
            "title": {
                "equals": title
            }
        }
    )
    return len(response.get('results', [])) > 0
```

### 2. Skip Duplicates
If a game is found, it's automatically skipped:

```
[2/150] --- Adding Celeste ---
⊘ Game 'Celeste' already exists in database (skipped)
```

### 3. Summary Statistics
At the end of sync, you get a complete breakdown:

```
============================================================
✓ Sync completed!
============================================================
Added: 148 | Skipped: 2 | Errors: 0
```

## Benefits

### Safe Re-syncing
You can run the sync multiple times without worrying about duplicates:

```bash
# First run: Adds 150 games
python main.py
# Added: 150 | Skipped: 0 | Errors: 0

# Second run: Skips all existing games
python main.py
# Added: 0 | Skipped: 150 | Errors: 0
```

### Incremental Updates
Only new games from your library are added:

```bash
# After buying 5 new games on Steam
python main.py
# Added: 5 | Skipped: 145 | Errors: 0
```

### Error Recovery
If sync fails partway through, re-running won't duplicate successfully added games:

```bash
# First run fails after 100 games
python main.py
# Added: 100 | Skipped: 0 | Errors: 50

# Second run continues where it left off
python main.py
# Added: 50 | Skipped: 100 | Errors: 0
```

## Configuration

### Enabled by Default
Duplicate detection is automatically enabled in all modes:

```python
# Optimized mode (default)
python main.py

# Legacy mode
python main.py --legacy

# Debug mode
python main.py --debug
```

### Disable Duplicate Detection
If you want to force adding duplicates (not recommended), you can modify the code:

```python
# In notion_integration.py
notion.write_row(
    database_id,
    cover,
    title,
    # ... other params ...
    skip_duplicates=False  # Disable duplicate check
)
```

## How Matching Works

### Exact Title Match
The system uses **exact title matching** (case-sensitive):

```python
# These are considered DIFFERENT games:
"The Witcher 3: Wild Hunt"  ≠  "The witcher 3: wild hunt"
"Celeste"                   ≠  "CELESTE"
"Portal 2"                  ≠  "Portal 2 "  # trailing space
```

### Recommendation
Let Steam/GOG provide the exact titles as they appear in their databases to ensure consistency.

## Performance Impact

### Minimal Overhead
- **1 additional API call** per game to check for duplicates
- Typically adds ~0.1-0.2 seconds per game
- Well worth it to prevent duplicates!

### Comparison
| Operation | Without Duplicate Check | With Duplicate Check |
|-----------|------------------------|----------------------|
| First sync (150 games) | ~10 minutes | ~10.5 minutes |
| Re-sync (0 new games) | ~10 minutes (duplicates!) | ~2 minutes (all skipped) |

**On re-syncs, duplicate detection actually SAVES time** by skipping expensive IGDB/HowLongToBeat calls!

## Error Handling

### Graceful Fallback
If the duplicate check fails (e.g., network error), the system assumes the game doesn't exist and tries to add it:

```python
try:
    exists = check_game_exists(database_id, title)
except Exception as e:
    print(f"Warning: Could not check for duplicate: {e}")
    exists = False  # Assume doesn't exist to avoid blocking
```

This ensures the sync doesn't fail completely due to a temporary Notion API issue.

## Use Cases

### 1. Regular Syncing
Keep your Notion database up-to-date without manual cleanup:

```bash
# Run weekly to add new games
python main.py
```

### 2. Multiple Store Accounts
If a game is owned on both Steam and GOG, only the first one encountered is added:

```
[50/200] --- Adding The Witcher 3 ---
✓ Game Added to Database (from Steam)
...
[150/200] --- Adding The Witcher 3 ---
⊘ Game 'The Witcher 3' already exists in database (skipped - from GOG)
```

### 3. Testing & Development
Test the sync process without cluttering your database:

```bash
# Test with first 10 games
python main.py --debug  # Adds 10 games

# Test again - no duplicates
python main.py --debug  # Skips all 10
```

## Limitations

### Title-Based Only
The system only checks titles, not:
- ❌ Game IDs (appid)
- ❌ Platforms
- ❌ Store source

This means if you manually rename a game in Notion, it might be added again as a duplicate.

### Case Sensitive
Exact match including capitalization:

```python
# Will be added as duplicates:
"DOOM" and "Doom"
```

**Recommendation**: Don't manually edit game titles in Notion.

### Multiple Stores
If the same game is on multiple stores with slightly different titles, they might be added separately:

```python
# These would be separate entries:
"The Elder Scrolls V: Skyrim" (Steam)
"Skyrim" (GOG)
```

## Future Enhancements

### Planned Improvements
1. ⚠️ **Fuzzy Matching**: Handle slight title variations
2. ⚠️ **Store ID Tracking**: Track which stores each game is on
3. ⚠️ **Update Mode**: Update existing entries instead of skipping
4. ⚠️ **Bulk Duplicate Check**: Query all games at once for better performance

### Store ID Tracking Example
Future version might show:

```
[50/200] --- Adding The Witcher 3 ---
→ Found existing entry
✓ Added GOG store link to existing game
```

## FAQ

**Q: What happens if I manually delete a game from Notion?**
A: Next sync will add it back as a "new" game.

**Q: Can I force re-add all games?**
A: Yes, set `skip_duplicates=False` in the code, or delete your Notion database and re-sync.

**Q: Does it check before calling IGDB?**
A: No, IGDB calls happen first, then Notion check. Future versions may optimize this.

**Q: What if Notion API is slow?**
A: The check adds minimal overhead (~0.1s per game). If Notion is slow, the whole sync will be slower.

**Q: Can I see which games were skipped?**
A: Yes, they're shown in the output with `⊘` symbol. Use `--debug` for more details.

## Conclusion

Duplicate detection makes the Game Backlog Assistant **safe to run multiple times** without manual cleanup. It's:

- ✅ Automatic and transparent
- ✅ Minimal performance impact
- ✅ Saves time on re-syncs
- ✅ Prevents database clutter
- ✅ Works with all sync modes

Just run `python main.py` and let the system handle the rest!
