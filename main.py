from notion_integration import NotionIntegration
from steam_integration import SteamIntegration
from gog_integration import GogIntegration
from IGDB import *
from howlongtobeat_integration import get_timetocompelete
from consts import *

def write_game(notion, title, debug=False):
    print('--- Adding ' + title + ' ---')
    failed = False
    consoles = list()

    consolesData = getGamePlatforms(title, debug)
    if consolesData is not None:
        for console in consolesData:
            consoles.append({'name': console})

    releaseDate = getGameRelease(title, debug)
    if releaseDate is None:
        releaseDate = datetime.datetime.now().strftime("%Y-%m-%d")
        failed = True

    genres = list()
    genresData = getGameGenres(title)
    if genresData is not None:
        for genre in genresData:
            genres.append({'name': genre})

    themes = getGameThemes(title)
    if themes is not None:
        for theme in themes:
            genres.append({'name': theme})

    if debug:
        debugGenres = "Game Genres:"
        for genre in genres:
            debugGenres += " " + genre["name"] + ","
        debugGenres = debugGenres[:-1]
        print(debugGenres)

    online = list()
    gameModeData = getGameModes(title)
    if gameModeData is not None:
        for gameMode in gameModeData:
            online.append({'name': gameMode})

    cover = getCoverLink(getGameID(title))
    if cover is None:
        cover = 'https://www.nctm.org/uploadedImages/Publications/TCM_Blog/checkerboard.png'

    length = get_timetocompelete(title)

    if not failed:
        notion.write_row(NOTION_DATABASE_ID, cover, title, consoles, releaseDate, online, genres, length, NOTION_PAGE_ID)
        print('Game Added to Database')
    else:
        print('Game Not Added to Database')
    return failed

def main():
    notion = NotionIntegration(auth_token=NOTION_TOKEN)

    integrations = []

    if STEAM_API_KEY and STEAM_USERID_64:
        integrations.append(SteamIntegration(api_key=STEAM_API_KEY, steamid=STEAM_USERID_64))

    if GOG_USERNAME and GOG_PASSWORD:
        integrations.append(GogIntegration())

    games = []

    for integration in integrations:
        owned_games = integration.get_owned_games()
        games.extend([game['name'] for game in owned_games])

    if not games:
        print("No games found in Steam or GOG libraries.")
        return

    for game in games:
        write_game(notion, game)

if __name__ == '__main__':
    main()
