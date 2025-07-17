import requests
import json
from datetime import datetime, timezone
from store_integration_protocol import StoreIntegrationProtocol
from consts import GOG_USERNAME, GOG_PROFILE_URL


class GogIntegration(StoreIntegrationProtocol):
    ACCESS_TOKEN_URL = "https://api.gog.com/user/accessToken.json"

    def __init__(self, username):
        self.username = username

    def get_owned_games(self):
        url = 'https://menu.gog.com/v1/account/licences'
        headers = {
            'Authorization': f'Bearer {self.bearer_token}'
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        return data['owned_games']

    def get_game_info(self, appid):
        url = f'https://www.gog.com/account/gameDetails/{appid}.json'

        headers = {
            'Authorization': f'Bearer {self.bearer_token}'
        }
        response = requests.get(url, headers=headers)
        try:
            data = response.json()
            if data and 'game' in data:
                return data['game']
            else:
                print(f"Error: 'game' key not found in response for appid {appid}")
                return None
        except ValueError:
            print(f"Error: Unable to parse JSON response for appid {appid}")
            return None
        except TypeError:
            print(f"Error: Response for appid {appid} is not JSON")
            return None

    def get_games_from_public_profile(self):
        """Recupera i giochi dal profilo pubblico di GOG."""
        url = GOG_PROFILE_URL.format(username=self.username)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Referer": "https://www.gog.com/"
        }

        params = {
            "sort": "alphabetically",
            "order": "asc",
            "page": 1
        }

        response = requests.get(url, params=params, headers=headers)

        return response.json() if response.status_code == 200 else None

# Esempio di utilizzo
if __name__ == "__main__":
    username = GOG_USERNAME
    gog_api = GogIntegration(username)
    owned_games = gog_api.get_games_from_public_profile()
    print("🎮 Giochi posseduti su GOG:")
    for game in owned_games:
        game_info = gog_api.get_game_info(game['id'])
        print(game_info['title'])
        print("📅 Data di rilascio:", game_info['release_date'])

