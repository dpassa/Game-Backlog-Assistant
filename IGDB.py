import requests, datetime, json
from consts import IGDB_API_V4_GAMES, IGDB_API_V4_GENRES, IGDB_API_V4_PLATFORMS,IGDB_API_V4_GAME_MODES, IGDB_API_V4_THEMES, IGDB_CLIENT_ID, IGDB_SECRET, IGDB_API_V4_WEBSITES,IGDB_API_V4_COVERS
from enum import Enum

class Platform(Enum):
    OFFICIAL = 1
    WIKIA = 2
    WIKIPEDIA = 3
    FACEBOOK = 4
    TWITTER = 5
    TWITCH = 6
    INSTAGRAM = 8
    YOUTUBE = 9
    IPHONE = 10
    IPAD = 11
    ANDROID = 12
    STEAM = 13
    REDDIT = 14
    ITCH = 15
    EPICGAMES = 16
    GOG = 17
    DISCORD = 18
    PS4 = 48
    NintendoSwitch = 130

class igdb_errors(str) :
    game_id = 'Failed to get Game ID',
    release_date ='Failed to get Release Date',
    genres = 'Failed to get Genres',
    themes = 'Failed to get Themes',
    platforms = 'Failed to get Platforms',
    game_modes= 'Failed to get Game Modes',
    websites='Failed to get Websites',
    cover_link= 'Failed to find Cover Link',
    save_cover= 'Failed to save Cover Image',
    download_image='Failed to download image'

clientID = IGDB_CLIENT_ID
secret = IGDB_SECRET

auth = requests.post(f'https://id.twitch.tv/oauth2/token?client_id={clientID}&client_secret={secret}&grant_type=client_credentials')

if auth.status_code == 200:
    access_token = auth.json()['access_token']    
else:
    print("Failed to fetch Authorization Token")

headers = {
    "Client-ID": clientID,
    "Authorization": f"Bearer {access_token}"
}

def api_send_post(endpoint, headers, data = 'name;'):
    response = requests.post(endpoint, headers=headers, data=f'fields {data}')
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def get_game_id(name):
    data = api_send_post(IGDB_API_V4_GAMES, headers, f'id; sort rating desc;where name = "{name}"; limit 1;')
    if data:
        try:
            return data[0]['id']
        except Exception:
            print(igdb_errors.game_id)
    else:
        print(igdb_errors.game_id)

def get_game_release(name, debug = False):
    data = api_send_post(IGDB_API_V4_GAMES, headers, f'first_release_date; sort rating desc;where name = "{name}"; limit 1;')
    if data:
        try:
            release = datetime.datetime.fromtimestamp(data[0]['first_release_date']).strftime("%Y-%m-%d")
            if debug:
                print('Game Release Date: ' + str(release))
            return release
        except Exception:
            print(igdb_errors.release_date)
    else:
        print(igdb_errors.release_date)

def get_game_genres(name, debug = False):
    data = api_send_post(IGDB_API_V4_GAMES, headers, f'genres; sort rating desc;where name = "{name}"; limit 1;')
    if not data:
        print(igdb_errors.genres)
        return
    try:
        game_data = data[0]
    except Exception:
        print(igdb_errors.genres)
        return

    genres_data = api_send_post(IGDB_API_V4_GENRES, headers)
    if genres_data:
        genres = []
        debugstring = "Game Genres:"
        for genre in genres_data:
            if 'genres' in game_data and genre['id'] in game_data['genres']:
                genres.append(genre['name'])
                debugstring += " " + genre['name']
        if debug:
            print(debugstring)
        return genres
    else:
        print(igdb_errors.genres)

def get_game_themes(name):
    data = api_send_post(IGDB_API_V4_GAMES, headers, f'themes; sort rating desc;where name = "{name}"; limit 1;')
    if not data:
        print(igdb_errors.themes)
        return
    try:
        game_data = data[0]
    except Exception:
        print(igdb_errors.themes)
        return

    themes_data = api_send_post(IGDB_API_V4_THEMES, headers)
    if themes_data:
        genres = []
        try:
            for genre in themes_data:
                if 'themes' in game_data and genre['id'] in game_data['themes']:
                    genres.append(genre['name'])
            return genres
        except Exception:
            print(igdb_errors.themes)
            return
    else:
        print(igdb_errors.themes)

def get_game_platforms(name, debug = False):
    data = api_send_post(IGDB_API_V4_GAMES, headers, f'platforms; sort rating desc;where name = "{name}"; limit 1;')
    if not data:
        print(igdb_errors.platforms)
        return
    try:
        game_data = data[0]
    except Exception:
        print(igdb_errors.platforms)
        return

    platforms_data = api_send_post(IGDB_API_V4_PLATFORMS, headers, 'name; limit 500;')
    if not platforms_data:
        print(igdb_errors.platforms)
        return

    platforms = []
    debugplatforms = "Game Platforms:"
    if 'platforms' in game_data and game_data['platforms']:
        for platform in platforms_data:
            if platform['id'] in game_data['platforms']:
                platforms.append(platform['name'])
                debugplatforms += " " + platform['name'] + ","
    if debug:
        debugplatforms = debugplatforms[:-1]
        print(debugplatforms)
    return platforms

def get_game_modes(name):
    data = api_send_post(IGDB_API_V4_GAMES, headers, f'game_modes; sort rating desc;where name = "{name}"; limit 1;')
    if not data:
        print(igdb_errors.game_modes)
        return
    try:
        game_data = data[0]
    except Exception:
        print(igdb_errors.game_modes)
        return

    modes_data = api_send_post(IGDB_API_V4_GAME_MODES, headers)
    if modes_data:
        gamemodes = []
        for gamemode in modes_data:
            if 'game_modes' in game_data and gamemode['id'] in game_data['game_modes']:
                gamemodes.append(gamemode['name'])
        return gamemodes
    else:
        print(igdb_errors.game_modes)

def get_game_websites(id):
    data = api_send_post(IGDB_API_V4_WEBSITES, headers, f'category,trusted,url; sort rating desc;where name = {id};')
    if not data:
        print(igdb_errors.websites)
        return []
    websites = []
    for website in data:
        if website.get('trusted'):
            websites.append({'category' : Platform(website['category']), 'url' : website['url']})
    return websites

def get_cover_link(id):
    data = api_send_post(IGDB_API_V4_COVERS, headers, f'url; where game = {id};')
    if data:
        try:
            key = data[0]['url'].split('t_thumb/')[1]
            return f"https://images.igdb.com/igdb/image/upload/t_cover_big/{key}"
        except Exception:
            print(igdb_errors.cover_link)
    else:
        print(igdb_errors.cover_link)

def save_cover(id, filename):
    data = api_send_post(IGDB_API_V4_COVERS, headers, f'url; sort rating desc;where name = {id};')
    if data:
        try:
            key = data[0]['url'].split('t_thumb/')[1]
            response = requests.get(f"https://images.igdb.com/igdb/image/upload/t_cover_big/{key}")
        except Exception:
            print(igdb_errors.download_image)
            return
    else:
        print(igdb_errors.download_image)
        return

    if response.status_code == 200:
        with open(f"{filename}.jpg", "wb") as file:
            file.write(response.content)
        print("Image downloaded successfully")
    else:
        print(igdb_errors.download_image)
