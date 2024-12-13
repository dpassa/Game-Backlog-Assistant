import requests
from consts import *

class SteamIntegration:
    def __init__(self, api_key, steamid):
        self.api_key = api_key
        self.steamid = steamid

    def get_owned_games(self):
        url = f'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={self.api_key}&steamid={self.steamid}&include_appinfo=true'
        response = requests.get(url)
        data = response.json()

        return data['response']['games']

    def get_game_info(self, appid):
        url = f'https://store.steampowered.com/api/appdetails?appids={appid}'
        response = requests.get(url)
        try:
            data = response.json()
            if data and str(appid) in data and 'data' in data[str(appid)]:
                return data[str(appid)]['data']
            else:
                print(f"Error: 'data' key not found in response for appid {appid}")
                return None
        except ValueError:
            print(f"Error: Unable to parse JSON response for appid {appid}")
            return None
        except TypeError:
            print(f"Error: Response for appid {appid} is not JSON")
            return None

