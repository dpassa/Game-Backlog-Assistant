# Design Principles

## Core Architecture

### Store Integration Protocol - Simple by Design

The `StoreIntegrationProtocol` has **only ONE method**:

```python
class StoreIntegrationProtocol(Protocol):
    def get_owned_games(self) -> list[NormalizedGame]
```

**Why?** Each integration is responsible for:
1. Fetching its own data from the store API
2. Normalizing that data internally
3. Returning complete, ready-to-use game objects

There is **NO** `get_game_info()` method in the protocol. Each integration decides internally how to fetch and structure data.

### Data Normalization - Inside, Not Outside

**✅ Correct Approach (Current Design)**:
```python
class SteamIntegration(StoreIntegrationProtocol):
    def get_owned_games(self) -> list[NormalizedGame]:
        # 1. Fetch games from Steam API
        raw_games = self._fetch_from_api()

        # 2. For each game, fetch details and normalize
        normalized_games = []
        for game in raw_games:
            game_info = self._fetch_game_details(game['appid'])

            # 3. Extract ALL available metadata
            normalized = {
                'appid': game['appid'],
                'name': game['name'],
                'notion_store_id': NOTION_STORE_STEAM_ID,
                'platforms': self._extract_platforms(game_info),
                'cover_url': game_info.get('header_image'),
                'release_date': self._extract_release_date(game_info),
                'genres': self._extract_genres(game_info),
                'game_modes': self._extract_game_modes(game_info),
            }

            # 4. Clean up None values
            normalized = {k: v for k, v in normalized.items() if v is not None}
            normalized_games.append(normalized)

        return normalized_games
```

**❌ Wrong Approach** (exposing internal methods):
```python
class SteamIntegration(StoreIntegrationProtocol):
    def get_owned_games(self) -> list:
        # Just returns bare minimum
        return [{'appid': x, 'name': y} for ...]

    def get_game_info(self, appid):  # ❌ Exposes internal implementation
        # Caller has to do normalization
        return raw_data
```

### Optimization - At the Write Level, Not Integration Level

The optimization (skipping IGDB calls) happens in `main.py`, NOT in the integrations:

**In store integrations**: Extract all available metadata
```python
# steam_integration.py
def get_owned_games(self):
    # Return games with as much data as possible
    return [
        {
            'name': 'Game',
            'platforms': ['PC'],      # ← Steam provides this
            'cover_url': '...',        # ← Steam provides this
            'release_date': '2020-01-01',  # ← Steam provides this
            'genres': ['Action'],      # ← Steam provides this
        }
    ]
```

**In main.py**: Use store data if available, otherwise call IGDB
```python
# main.py - write_game_optimized()
def write_game_optimized(notion, game_data, debug=False):
    # Use store data if it exists
    platforms = game_data.get('platforms') or call_igdb_platforms()
    cover = game_data.get('cover_url') or call_igdb_cover()
    release_date = game_data.get('release_date') or call_igdb_release()
    genres = game_data.get('genres') or call_igdb_genres()

    # Write to Notion
    notion.write_row(...)
```

## Key Benefits

### 1. Simple Protocol
- Only one method to implement
- Easy to understand
- Hard to implement incorrectly

### 2. Encapsulation
- Each integration is self-contained
- Internal methods (like `_fetch_game_details`) are private
- No need to expose implementation details

### 3. Flexibility
- Steam can call its API however it wants
- GOG can structure its fetching differently
- As long as they return `NormalizedGame`, it works

### 4. Optimization
- Integrations don't need to know about IGDB
- They just provide what they have
- `main.py` handles the "use store data or call IGDB" logic

## Example: Adding a New Store

```python
# epic_integration.py
from store_integration_protocol import StoreIntegrationProtocol, NormalizedGame

class EpicGamesIntegration(StoreIntegrationProtocol):
    def __init__(self, api_key):
        self.api_key = api_key

    def get_owned_games(self) -> list[NormalizedGame]:
        """
        Fetch and normalize Epic Games library.
        All data fetching happens here.
        """
        # 1. Fetch from Epic API (however you want)
        raw_games = requests.get('https://epic-api.com/games', ...)

        # 2. Normalize each game
        normalized_games = []
        for game in raw_games.json()['items']:
            normalized = {
                'appid': game['id'],
                'name': game['title'],
                'notion_store_id': NOTION_STORE_EPIC_ID,

                # Epic provides rich metadata - extract it!
                'platforms': game.get('platforms', []),
                'cover_url': game.get('images', {}).get('tall'),
                'release_date': game.get('releaseDate'),
                'genres': [g['name'] for g in game.get('categories', [])],
                'game_modes': self._extract_game_modes(game),
            }

            # Remove None values
            normalized = {k: v for k, v in normalized.items() if v is not None}
            normalized_games.append(normalized)

        return normalized_games

    def _extract_game_modes(self, game: dict) -> list[str] | None:
        """Private helper method - not exposed in protocol"""
        # Your extraction logic here
        pass
```

That's it! No need to implement `get_game_info()` or expose any other methods.

## Data Flow Summary

```
┌──────────────────────────────────────────────────────────────┐
│ Store Integration (e.g., Steam, GOG, Epic)                   │
│                                                               │
│  get_owned_games():                                           │
│    1. Fetch raw data from store API                          │
│    2. Extract ALL available metadata                         │
│    3. Normalize to NormalizedGame format                     │
│    4. Return complete game objects                           │
│                                                               │
│  All logic is INTERNAL - no exposed helper methods           │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 │ Returns: list[NormalizedGame]
                 │
                 v
┌──────────────────────────────────────────────────────────────┐
│ main.py - write_game_optimized()                             │
│                                                               │
│  For each field:                                              │
│    - Check if store provided it                              │
│    - If yes: use store data                                  │
│    - If no: call IGDB API                                    │
│                                                               │
│  This is where optimization happens!                         │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 v
┌──────────────────────────────────────────────────────────────┐
│ Notion Database                                               │
│                                                               │
│  Game entry with complete metadata                           │
└──────────────────────────────────────────────────────────────┘
```

## Anti-Patterns to Avoid

### ❌ DON'T: Expose `get_game_info()` in protocol
```python
class StoreIntegrationProtocol(Protocol):
    def get_owned_games(self) -> list
    def get_game_info(self, appid) -> dict  # ❌ Too much exposure
```

**Why not?** This forces all integrations to implement a method they might not need, and exposes internal implementation details.

### ❌ DON'T: Return minimal data from integrations
```python
def get_owned_games(self):
    return [{'appid': 123, 'name': 'Game'}]  # ❌ Missing opportunities
```

**Why not?** You're forcing unnecessary IGDB calls when the store API already has the data.

### ❌ DON'T: Do optimization inside integrations
```python
def get_owned_games(self):
    games = []
    for game in raw_games:
        # ❌ Don't check IGDB here
        if not game.get('cover'):
            game['cover'] = call_igdb_cover()
    return games
```

**Why not?** Integrations shouldn't know about IGDB. That's `main.py`'s job.

## Best Practices

### ✅ DO: Keep protocol simple
```python
class StoreIntegrationProtocol(Protocol):
    def get_owned_games(self) -> list[NormalizedGame]
```

### ✅ DO: Extract all available data in integrations
```python
def get_owned_games(self):
    # Include everything the store API provides
    return [
        {
            'appid': ...,
            'name': ...,
            'platforms': [...],      # If available
            'cover_url': '...',       # If available
            'release_date': '...',    # If available
            'genres': [...],          # If available
            'game_modes': [...],      # If available
        }
    ]
```

### ✅ DO: Let main.py handle optimization
```python
# main.py
platforms = game_data.get('platforms') or handle_game_platforms(title)
```

### ✅ DO: Use private methods for internal logic
```python
class SteamIntegration:
    def get_owned_games(self):
        # Public method
        pass

    def _fetch_from_api(self):
        # Private helper - not in protocol
        pass

    def _extract_platforms(self, game_info):
        # Private helper - not in protocol
        pass
```

## Summary

1. **Protocol**: One method (`get_owned_games()`)
2. **Integrations**: Self-contained, normalize internally
3. **Optimization**: Happens in `main.py`, not in integrations
4. **Simplicity**: No exposed implementation details

This design is clean, simple, and easy to extend!
