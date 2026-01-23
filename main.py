from notion_integration import NotionIntegration
from steam_integration import SteamIntegration
from gog_integration import GogIntegration
from IGDB import get_game_platforms, get_game_release, get_game_genres, get_game_themes, get_game_modes, get_cover_link, get_game_id
from howlongtobeat_integration import get_timetocompelete
from consts import NOTION_DATABASE_ID, STEAM_API_KEY, STEAM_USERID_64, GOG_PUBLIC_USERNAME, NOTION_TOKEN
import datetime

def handle_game_platforms(title, debug=False):
    consoles = []
    consoles_data = get_game_platforms(title, debug)
    if consoles_data is not None:
        for console in consoles_data:
            consoles.append({'name': console})
    return consoles

def handle_game_release(title, debug=False):
    release_date = get_game_release(title, debug)
    if release_date is None:
        release_date = datetime.datetime.now().strftime("%Y-%m-%d")
        return release_date, True  # True indica che è fallito
    return release_date, False

def handle_game_genres(title, debug=False):
    genres = []
    genres_data = get_game_genres(title)
    if genres_data is not None:
        for genre in genres_data:
            genres.append({'name': genre})
    
    themes = get_game_themes(title)
    if themes is not None:
        for theme in themes:
            genres.append({'name': theme})
    
    if debug and genres:
        debug_genres = "Game Genres:"
        for genre in genres:
            debug_genres += " " + genre["name"] + ","
        debug_genres = debug_genres[:-1]
        print(debug_genres)
    
    return genres

def handle_game_modes(title, debug=False):
    """
    Get game modes for a given title.

    Args:
        title: Game title
        debug: Enable debug output (default: False)

    Returns:
        List of game mode dictionaries
    """
    online = []
    game_mode_data = get_game_modes(title)
    if game_mode_data is not None:
        for game_mode in game_mode_data:
            online.append({'name': game_mode})
    return online

def handle_game_cover(title):
    cover = get_cover_link(get_game_id(title))
    if cover is None:
        cover = 'https://www.nctm.org/uploadedImages/Publications/TCM_Blog/checkerboard.png'
    return cover

def handle_game_length(title):
    return get_timetocompelete(title)




def _get_field_or_fallback(game_data, field_name, title, fallback_func, debug=False):
    """
    Get field from game_data or use fallback function.

    Args:
        game_data: Normalized game dictionary
        field_name: Field name to check in game_data
        title: Game title for fallback function
        fallback_func: Function to call if field not in game_data
        debug: Enable debug output

    Returns:
        Tuple of (value, source) where source is 'store' or 'igdb'
    """
    if field_name in game_data and game_data[field_name]:
        if debug:
            value_str = str(game_data[field_name])
            if len(value_str) > 60:
                value_str = value_str[:60] + '...'
            print(f'✓ Using {field_name} from store: {value_str}')
        return game_data[field_name], 'store'

    return fallback_func(title, debug) if debug else fallback_func(title), 'igdb'


def _convert_to_notion_multiselect(items):
    """Convert list of strings to Notion multi-select format"""
    if not items:
        return []
    return [{'name': item} for item in items]


def _print_optimization_stats(sources_used, debug):
    """Print optimization statistics if debug is enabled"""
    if not debug:
        return

    store_count = len(sources_used['store'])
    igdb_count = len(sources_used['igdb'])
    total_fields = store_count + igdb_count

    if total_fields > 0:
        optimization_pct = (store_count / total_fields) * 100
        print(f'📊 Optimization: {store_count}/{total_fields} fields from store ({optimization_pct:.0f}%)')
        if sources_used['store']:
            print(f'   Store provided: {", ".join(sources_used["store"])}')
        if sources_used['igdb']:
            print(f'   IGDB called for: {", ".join(sources_used["igdb"])}')


def write_game(notion, game_data, store_integration=None, debug=False, game_status='new', page_id=None, existing_data=None):
    """
    Write game to Notion or update existing game, using store data when available.

    Args:
        notion: NotionIntegration instance
        game_data: Normalized game dictionary from store integration
        store_integration: Store integration instance (SteamIntegration, GogIntegration, etc.)
        debug: Enable debug output
        game_status: Pre-computed status ('completed', 'exists', 'new') from lookup
        page_id: Pre-computed page_id for existing games
        existing_data: Existing game data from Notion lookup (for comparison)

    Returns:
        str: Status - 'added', 'updated', 'skipped', or 'error'
    """
    title = game_data['name']
    external_id = game_data.get('external_id', '')

    # Handle completed games - should be skipped before reaching here, but included for safety
    if game_status == 'completed':
        print(f'Skipping {title} (already Complete)')
        return 'skipped'

    if game_status == 'exists':
        print(f'--- Checking {title} ---')
        # Game exists - update status and achievements only if changed
        try:
            # Fetch enriched data from store (achievements, status)
            if store_integration and hasattr(store_integration, 'get_enriched_game_data'):
                enriched_data = store_integration.get_enriched_game_data(external_id)

                if enriched_data:
                    new_achievement_pct = enriched_data.get('achievement_percentage', 0)
                    new_status = enriched_data.get('status', 'Backlog')

                    # Get existing values from Notion lookup
                    existing_status = existing_data.get('status', '') if existing_data else ''
                    existing_achievements = existing_data.get('achievements', 0) if existing_data else 0

                    # Compare with existing data - skip if no changes
                    status_changed = new_status != existing_status
                    achievements_changed = new_achievement_pct != existing_achievements

                    if debug:
                        print(f'  Existing: status={existing_status}, achievements={existing_achievements}%')
                        print(f'  New: status={new_status}, achievements={new_achievement_pct}%')

                    if not status_changed and not achievements_changed:
                        print(f'⊘ No changes detected, skipping update')
                        return 'skipped'

                    # Log what changed
                    changes = []
                    if status_changed:
                        changes.append(f'status: {existing_status} → {new_status}')
                    if achievements_changed:
                        changes.append(f'achievements: {existing_achievements}% → {new_achievement_pct}%')
                    print(f'📝 Changes: {", ".join(changes)}')

                    # Update Notion with new status and achievements
                    success, message = notion.update_game_status_and_achievements(
                        page_id,
                        status=new_status,
                        achievement_percentage=new_achievement_pct
                    )

                    if success:
                        print(f'✓ Game Updated')
                        return 'updated'
                    else:
                        print(f'⚠ Update failed: {message}')
                        return 'error'
                else:
                    print('⊘ No enriched data available, skipping update')
                    return 'skipped'
            else:
                print('⊘ Store does not support status sync, skipping update')
                return 'skipped'

        except Exception as e:
            print(f'✗ Error updating: {e}')
            return 'error'

    else:  # game_status == 'new'
        print(f'--- Adding {title} ---')
        # Game doesn't exist - add it with full details
        sources_used = {'store': [], 'igdb': []}

        try:
            # Get platforms
            platforms_data, platforms_source = _get_field_or_fallback(
                game_data, 'platforms', title, handle_game_platforms, debug
            )
            consoles = _convert_to_notion_multiselect(platforms_data) if platforms_source == 'store' else platforms_data
            sources_used[platforms_source].append('platforms')

            # Get release date
            if 'release_date' in game_data and game_data['release_date']:
                release_date = (game_data['release_date'], False)
                sources_used['store'].append('release_date')
                if debug:
                    print(f'✓ Using release_date from store: {game_data["release_date"]}')
            else:
                release_date = handle_game_release(title, debug)
                sources_used['igdb'].append('release_date')

            # Get genres
            genres_data, genres_source = _get_field_or_fallback(
                game_data, 'genres', title, handle_game_genres, debug
            )
            genres = _convert_to_notion_multiselect(genres_data) if genres_source == 'store' else genres_data
            sources_used[genres_source].append('genres')

            # Get game modes
            modes_data, modes_source = _get_field_or_fallback(
                game_data, 'game_modes', title, handle_game_modes, debug
            )
            online = _convert_to_notion_multiselect(modes_data) if modes_source == 'store' else modes_data
            sources_used[modes_source].append('game_modes')

            # Get cover
            cover, cover_source = _get_field_or_fallback(
                game_data, 'cover_url', title, handle_game_cover, debug
            )
            sources_used[cover_source].append('cover')

            # HowLongToBeat: Always required (no store provides this)
            length = handle_game_length(title)

            # Get initial status and achievements from store if available
            initial_status = 'Backlog'
            achievement_pct = 0

            if store_integration and hasattr(store_integration, 'get_enriched_game_data'):
                enriched_data = store_integration.get_enriched_game_data(external_id)
                if enriched_data:
                    achievement_pct = enriched_data.get('achievement_percentage', 0)
                    initial_status = enriched_data.get('status', 'Backlog')
                    print(f'📊 Initial Achievements: {achievement_pct}%')
                    print(f'🎯 Initial Status: {initial_status}')

            # Write to Notion with initial status and achievements
            created, message = notion.write_row(
                NOTION_DATABASE_ID,
                cover,
                title,
                consoles,
                release_date,
                online,
                genres,
                length,
                game_data['notion_store_id'],
                external_id=external_id,
                initial_status=initial_status,
                achievement_percentage=achievement_pct
            )

            if created:
                _print_optimization_stats(sources_used, debug)
                print('✓ Game Added to Database')
                return 'added'
            else:
                print(f'⊘ {message}')
                return 'skipped'

        except Exception as e:
            print(f'✗ Error: {e}')
            return 'error'


def _initialize_integrations():
    """Initialize store integrations based on available credentials"""
    integrations = []

    if STEAM_API_KEY and STEAM_USERID_64:
        integrations.append(SteamIntegration(api_key=STEAM_API_KEY, steamid=STEAM_USERID_64))

    if GOG_PUBLIC_USERNAME:
        integrations.append(GogIntegration(username=GOG_PUBLIC_USERNAME))

    return integrations


def _fetch_all_games(integrations):
    """Fetch games from all store integrations and return with integration mapping"""
    games = []
    game_to_integration = {}

    print(f"Fetching games from {len(integrations)} store(s)...")
    for integration in integrations:
        store_name = integration.__class__.__name__.replace('Integration', '')
        print(f"  Loading {store_name} library...")
        owned_games = integration.get_owned_games()
        print(f"  Found {len(owned_games)} games in {store_name}")

        # Map each game to its integration for later use
        for game in owned_games:
            game_key = f"{game.get('external_id', '')}_{game.get('store_name', '')}"
            game_to_integration[game_key] = integration

        games.extend(owned_games)

    return games, game_to_integration


def _normalize_notion_id(notion_id):
    """
    Normalize Notion ID by removing dashes for consistent comparison.

    Notion IDs can be returned in different formats:
    - With dashes: 12345678-1234-1234-1234-123456789abc
    - Without dashes: 123456781234123412341234567890abc

    Args:
        notion_id: Notion page/database ID

    Returns:
        Normalized ID without dashes (lowercase)
    """
    if not notion_id:
        return ''
    return str(notion_id).replace('-', '').lower()


def _build_notion_game_lookup(notion, database_id):
    """
    Pre-fetch all games from Notion and build lookup structures.

    This optimization reduces N individual API queries to a single paginated query,
    significantly reducing API calls when processing large game libraries.

    Args:
        notion: NotionIntegration instance
        database_id: Notion database ID

    Returns:
        Tuple of:
        - lookup_dict: Dict mapping (external_id, normalized_store_id) -> game_data
        - completed_keys: Set of (external_id, normalized_store_id) tuples for completed games
    """
    try:
        print("Pre-fetching all games from Notion...")
        all_games = notion.get_all_games(database_id)
        print(f"Retrieved {len(all_games)} games from Notion")

        lookup_dict = {}
        completed_keys = set()

        for game in all_games:
            external_id = game.get('external_id', '')
            store_id = _normalize_notion_id(game.get('store_id', ''))
            status = game.get('status', '')
            achievements = game.get('achievements', 0)

            if external_id and store_id:
                key = (external_id, store_id)
                lookup_dict[key] = game

                # Consider complete if status is "Complete" OR achievements are 100%
                if status == 'Complete' or achievements == 100:
                    completed_keys.add(key)

        print(f"Lookup stats: {len(lookup_dict)} indexed, {len(completed_keys)} completed")

        # Debug: show sample keys for verification
        if lookup_dict:
            sample_keys = list(lookup_dict.keys())[:3]
            print(f"Sample lookup keys: {sample_keys}")

        return lookup_dict, completed_keys

    except Exception as e:
        print(f"Warning: Could not pre-fetch Notion games: {e}")
        print("Falling back to per-game lookup (slower)")
        return {}, set()


def _check_game_in_lookup(game_data, lookup_dict, completed_keys, debug=False):
    """
    Check game status using pre-built lookup structures.

    Provides O(1) lookup instead of individual API calls for each game.

    Args:
        game_data: Normalized game from store integration
        lookup_dict: Pre-built (external_id, normalized_store_id) -> game_data dict
        completed_keys: Set of completed game keys
        debug: Enable debug output for key matching

    Returns:
        Tuple of (status, page_id):
        - ('completed', page_id): Game is complete, skip entirely
        - ('exists', page_id): Game exists but not complete, update needed
        - ('new', None): Game doesn't exist, add it
    """
    external_id = game_data.get('external_id', '')
    store_id = _normalize_notion_id(game_data.get('notion_store_id', ''))

    if not external_id or not store_id:
        if debug:
            print(f"  DEBUG: Missing external_id={external_id} or store_id={store_id}")
        return ('new', None)

    key = (external_id, store_id)

    if debug:
        print(f"  DEBUG: Looking for key {key}")

    if key in completed_keys:
        page_id = lookup_dict[key].get('page_id')
        return ('completed', page_id)

    if key in lookup_dict:
        page_id = lookup_dict[key].get('page_id')
        return ('exists', page_id)

    if debug:
        # Show similar keys that might match
        similar = [k for k in lookup_dict.keys() if k[0] == external_id]
        if similar:
            print(f"  DEBUG: Found similar external_id but different store: {similar}")

    return ('new', None)


def _process_game(notion, game, game_to_integration, lookup_dict, completed_keys, debug):
    """
    Process a single game and write to Notion.

    Args:
        notion: NotionIntegration instance
        game: Normalized game data from store
        game_to_integration: Mapping of game keys to store integrations
        lookup_dict: Pre-built Notion game lookup
        completed_keys: Set of completed game keys
        debug: Enable debug output

    Returns:
        str: Status - 'added', 'updated', 'skipped', or 'error'
    """
    # Check game status using pre-built lookup (O(1) operation)
    game_status, page_id = _check_game_in_lookup(game, lookup_dict, completed_keys, debug)

    # Skip completed games entirely - no store API calls needed!
    if game_status == 'completed':
        print(f'Skipping {game.get("name", "Unknown")} (Complete)')
        return 'skipped'

    # Get existing data from lookup for comparison (avoids unnecessary Notion updates)
    external_id = game.get('external_id', '')
    store_id = _normalize_notion_id(game.get('notion_store_id', ''))
    lookup_key = (external_id, store_id)
    existing_data = lookup_dict.get(lookup_key)

    # Get the store integration for this game
    game_key = f"{external_id}_{game.get('store_name', '')}"
    store_integration = game_to_integration.get(game_key)

    return write_game(
        notion, game,
        store_integration=store_integration,
        debug=debug,
        game_status=game_status,
        page_id=page_id,
        existing_data=existing_data
    )


def main(debug=False):
    """
    Main entry point for syncing games to Notion.

    Optimized flow:
    1. Pre-fetch all games from Notion (single paginated query)
    2. Build lookup structures for fast existence checking
    3. Fetch games from store APIs
    4. Process games: skip completed, update existing, add new

    Args:
        debug: Enable debug output (default: False)
    """
    integrations = _initialize_integrations()

    if not integrations:
        print("No store integrations configured.")
        print("Please set up Steam or GOG credentials in .env file.")
        return

    notion = NotionIntegration(NOTION_TOKEN)

    # OPTIMIZATION: Pre-fetch all Notion games BEFORE store API calls
    lookup_dict, completed_keys = _build_notion_game_lookup(notion, NOTION_DATABASE_ID)

    # Now fetch from store APIs
    games, game_to_integration = _fetch_all_games(integrations)

    if not games:
        print("No games found in any library.")
        return

    # Calculate actual work needed before processing
    new_count = 0
    update_count = 0
    skip_count = 0

    for game in games:
        status, _ = _check_game_in_lookup(game, lookup_dict, completed_keys)
        if status == 'completed':
            skip_count += 1
        elif status == 'exists':
            update_count += 1
        else:
            new_count += 1

    print(f"\nProcessing Summary:")
    print(f"  Total from stores: {len(games)}")
    print(f"  Complete (skip): {skip_count}")
    print(f"  Existing (update): {update_count}")
    print(f"  New (add): {new_count}")
    print(f"  API calls saved: {skip_count}")
    print("\nProcessing games (optimized mode)\n")

    # Track statistics
    stats = {'added': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

    # Process each game with optimized lookup
    for i, game in enumerate(games, 1):
        print(f"\n[{i}/{len(games)}]", end=' ')

        try:
            status = _process_game(
                notion, game, game_to_integration,
                lookup_dict, completed_keys, debug
            )
            stats[status] = stats.get(status, 0) + 1

        except Exception as e:
            print(f"Error processing {game.get('name', 'unknown')}: {e}")
            stats['errors'] += 1
            if debug:
                import traceback
                traceback.print_exc()

    print("\n" + "="*60)
    print("Sync completed!")
    print("="*60)
    print(f"Added: {stats['added']} | Updated: {stats['updated']} | Skipped: {stats['skipped']} | Errors: {stats['errors']}")


if __name__ == '__main__':
    import sys

    # Parse command line arguments
    debug = '--debug' in sys.argv

    main(debug=debug)
