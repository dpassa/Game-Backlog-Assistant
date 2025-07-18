import requests
import json
from store_integration_protocol import StoreIntegrationProtocol
from consts import GOG_PUBLIC_USERNAME, GOG_PROFILE_URL


class GogIntegration(StoreIntegrationProtocol):
    def __init__(self, username):
        self.username = username
        self.session = requests.Session()
        self.session.get('https://www.gog.com/')

    def get_game_info(self, appid):
        url = f'https://www.gog.com/account/gameDetails/{appid}.json'

        response = self.session.get(url)
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

    def get_games_from_public_profile(self, page=1):
        url = GOG_PROFILE_URL.format(username=self.username)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
            "Accept": "application/hal+json, application/json, */*",
            "Referer": "https://www.gog.com/u/BifcottoLol/games",
            "X-Requested-With": "XMLHttpRequest"
        }

        params = {
            "sort": "recent_playtime",
            "order": "desc",
            "page": page
        }
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Errore HTTP: {response.status_code}")
                return None
                
        except json.JSONDecodeError as e:
            print(f"Errore parsing JSON: {e}")
            print(f"Contenuto ricevuto: {response.text[:500]}")
            return None
        except Exception as e:
            print(f"Errore generico: {e}")
            return None
        
        return response.content.json() if response.status_code == 200 else None

# Esempio di utilizzo
if __name__ == "__main__":
    username = GOG_PUBLIC_USERNAME
    gog_api = GogIntegration(username)
    owned_games = gog_api.get_games_from_public_profile()
    print("🎮 Giochi posseduti su GOG:")
    for game in owned_games:
        game_info = gog_api.get_game_info(game['id'])
        print(game_info['title'])
        print("📅 Data di rilascio:", game_info['release_date'])