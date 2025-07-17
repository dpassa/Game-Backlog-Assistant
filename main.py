from notion_integration import NotionIntegration
from steam_integration import SteamIntegration
from gog_integration import GogIntegration
from IGDB import get_game_platforms, get_game_release, get_game_genres, get_game_themes, get_game_modes, get_cover_link, get_game_id
from howlongtobeat_integration import get_timetocompelete
from consts import NOTION_DATABASE_ID, NOTION_PAGE_ID, STEAM_API_KEY, STEAM_USERID_64, GOG_USERNAME, NOTION_TOKEN
import datetime

def write_game(notion, title, debug=False):
    print('--- Adding ' + title + ' ---')
    failed = False
    consoles = []

    consoles_data = get_game_platforms(title, debug)
    if consoles_data is not None:
        for console in consoles_data:
            consoles.append({'name': console})

    release_date = get_game_release(title, debug)
    if release_date is None:
        release_date = datetime.datetime.now().strftime("%Y-%m-%d")
        failed = True

    genres = []
    genres_data = get_game_genres(title)
    if genres_data is not None:
        for genre in genres_data:
            genres.append({'name': genre})

    themes = get_game_themes(title)
    if themes is not None:
        for theme in themes:
            genres.append({'name': theme})

    if debug:
        debug_genres = "Game Genres:"
        for genre in genres:
            debug_genres += " " + genre["name"] + ","
        debug_genres = debug_genres[:-1]
        print(debug_genres)

    online = []
    game_mode_data = get_game_modes(title)
    if game_mode_data is not None:
        for game_mode in game_mode_data:
            online.append({'name': game_mode})

    cover = get_cover_link(get_game_id(title))
    if cover is None:
        cover = 'https://www.nctm.org/uploadedImages/Publications/TCM_Blog/checkerboard.png'

    length = get_timetocompelete(title)

    if not failed:
        notion.write_row(NOTION_DATABASE_ID, cover, title, consoles, release_date, online, genres, length, NOTION_PAGE_ID)
        print('Game Added to Database')
    else:
        print('Game Not Added to Database')
    return failed

def main():
    integrations = []

    if STEAM_API_KEY and STEAM_USERID_64:
        integrations.append(SteamIntegration(api_key=STEAM_API_KEY, steamid=STEAM_USERID_64))

    if GOG_USERNAME:
        integrations.append(GogIntegration(username=GOG_USERNAME))

    games = []

    for integration in integrations:
        owned_games = integration.get_owned_games()
        games.extend([game['name'] for game in owned_games])

    if not games:
        print("No games found in Steam or GOG libraries.")
        return

    notion = NotionIntegration(NOTION_TOKEN)
    for game in games:
        write_game(notion, game)

if __name__ == '__main__':
    main()
