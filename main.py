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


def write_game(notion, game_data, store_integration=None, debug=False):
    """
    Write game to Notion or update existing game, using store data when available.

    Args:
        notion: NotionIntegration instance
        game_data: Normalized game dictionary from store integration
        store_integration: Store integration instance (SteamIntegration, GogIntegration, etc.)
        debug: Enable debug output

    Returns:
        str: Status - 'added', 'updated', 'skipped', or 'error'
    """
    title = game_data['name']
    external_id = game_data.get('external_id', '')
    store_relation_id = game_data.get('notion_store_id', '')

    # Check if game already exists in Notion
    exists, page_id = notion.check_game_exists_by_external_id(
        NOTION_DATABASE_ID,
        external_id,
        store_relation_id
    ) if external_id and store_relation_id else (False, None)

    if exists:
        print(f'--- Updating {title} ---')
        # Game exists - update status and achievements if not complete
        try:
            # Get current status from Notion to check if already complete
            # For now, we'll attempt to update all existing games

            # Fetch enriched data from store (achievements, status)
            if store_integration and hasattr(store_integration, 'get_enriched_game_data'):
                enriched_data = store_integration.get_enriched_game_data(external_id)

                if enriched_data:
                    achievement_pct = enriched_data.get('achievement_percentage', 0)
                    new_status = enriched_data.get('status', 'Backlog')

                    print(f'📊 Achievements: {achievement_pct}%')
                    print(f'🎯 Status: {new_status}')

                    # Update Notion with new status and achievements
                    success, message = notion.update_game_status_and_achievements(
                        page_id,
                        status=new_status,
                        achievement_percentage=achievement_pct
                    )

                    if success:
                        print(f'✓ Game Updated: {message}')
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

    else:
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


def _process_game(notion, game, game_to_integration, debug):
    """
    Process a single game and write to Notion.

    Returns:
        str: Status - 'added', 'updated', 'skipped', or 'error'
    """
    # Get the store integration for this game
    game_key = f"{game.get('external_id', '')}_{game.get('store_name', '')}"
    store_integration = game_to_integration.get(game_key)

    return write_game(notion, game, store_integration=store_integration, debug=debug)


def main(debug=False):
    """
    Main entry point for syncing games to Notion.

    This function now handles both adding new games and updating existing ones
    with status and achievement data.

    Args:
        debug: Enable debug output (default: False)
    """
    integrations = _initialize_integrations()

    if not integrations:
        print("No store integrations configured.")
        print("Please set up Steam or GOG credentials in .env file.")
        return

    games, game_to_integration = _fetch_all_games(integrations)

    if not games:
        print("No games found in any library.")
        return

    print(f"\nTotal games to process: {len(games)}")
    print("🚀 Processing games (unified add/update mode)\n")

    notion = NotionIntegration(NOTION_TOKEN)

    # Track statistics
    stats = {'added': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

    # Process each game
    for i, game in enumerate(games, 1):
        print(f"\n[{i}/{len(games)}]", end=' ')

        try:
            status = _process_game(notion, game, game_to_integration, debug)
            stats[status] = stats.get(status, 0) + 1

        except Exception as e:
            print(f"❌ Error processing {game.get('name', 'unknown')}: {e}")
            stats['errors'] += 1
            if debug:
                import traceback
                traceback.print_exc()

    print("\n" + "="*60)
    print("✓ Sync completed!")
    print("="*60)
    print(f"Added: {stats['added']} | Updated: {stats['updated']} | Skipped: {stats['skipped']} | Errors: {stats['errors']}")


if __name__ == '__main__':
    import sys

    # Parse command line arguments
    debug = '--debug' in sys.argv

    main(debug=debug)
