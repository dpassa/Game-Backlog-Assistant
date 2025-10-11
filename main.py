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

def handle_game_modes(title):
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


def write_game(notion, game_data, debug=False):
    """
    Write game to Notion, using store data when available to minimize IGDB calls.

    Args:
        notion: NotionIntegration instance
        game_data: Normalized game dictionary from store integration
        debug: Enable debug output

    Returns:
        str: Status - 'added', 'skipped', or 'error'
    """
    title = game_data['name']
    print(f'--- Adding {title} ---')

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

        # Write to Notion (with duplicate checking)
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
            skip_duplicates=True  # Skip if already exists
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
    """Fetch games from all store integrations"""
    games = []

    print(f"Fetching games from {len(integrations)} store(s)...")
    for integration in integrations:
        store_name = integration.__class__.__name__.replace('Integration', '')
        print(f"  Loading {store_name} library...")
        owned_games = integration.get_owned_games()
        print(f"  Found {len(owned_games)} games in {store_name}")
        games.extend(owned_games)

    return games


def _process_game(notion, game, debug):
    """
    Process a single game and write to Notion.

    Returns:
        str: Status - 'added', 'skipped', or 'error'
    """
    return write_game(notion, game, debug=debug)


def main(debug=False):
    """
    Main entry point for syncing games to Notion.

    Args:
        debug: Enable debug output (default: False)
    """
    integrations = _initialize_integrations()

    if not integrations:
        print("No store integrations configured.")
        print("Please set up Steam or GOG credentials in .env file.")
        return

    games = _fetch_all_games(integrations)

    if not games:
        print("No games found in any library.")
        return

    print(f"\nTotal games to process: {len(games)}")
    print("🚀 Processing games (optimized mode)\n")

    notion = NotionIntegration(NOTION_TOKEN)

    # Track statistics
    stats = {'added': 0, 'skipped': 0, 'errors': 0}

    # Process each game
    for i, game in enumerate(games, 1):
        print(f"\n[{i}/{len(games)}]", end=' ')

        try:
            status = _process_game(notion, game, debug)
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
    print(f"Added: {stats['added']} | Skipped: {stats['skipped']} | Errors: {stats['errors']}")


if __name__ == '__main__':
    import sys

    # Parse command line arguments
    debug = '--debug' in sys.argv

    main(debug=debug)
