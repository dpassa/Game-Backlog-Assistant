import requests
import json
from datetime import datetime, timezone
from store_integration_protocol import StoreIntegrationProtocol
from gog_auth_selenium import GogAuthSelenium  # Importiamo la classe per il login con Selenium
from consts import GOG_USERNAME, GOG_PASSWORD, COOKIE_FILE

def load_cookies_into_session(session, cookie_file="cookies.json"):
    """Carica i cookie salvati in una sessione requests e verifica se sono scaduti."""
    try:
        with open(cookie_file, "r") as f:
            cookies = json.load(f)
    except FileNotFoundError:
        print("❌ Errore: il file dei cookie non esiste. Esegui prima il login con Selenium.")
        return False

    if not cookies:
        print("❌ Errore: i cookie non sono presenti. Esegui prima il login con Selenium.")
        return False

    for cookie in cookies:
        expiry = cookie.get("expiry")
        if verify_expiration(expiry):
            print("❌ Cookie scaduto:", cookie["name"])
            return False

        session.cookies.set(
            name=cookie["name"],
            value=cookie["value"],
            domain=cookie.get("domain", ".gog.com"),
            path=cookie.get("path", "/"),
            secure=cookie.get("secure", False),
        )

    print("✅ Cookie caricati nella sessione requests!")
    print(session.cookies.get_dict())
    return True

def verify_expiration(expiry):
    if not expiry:
        return False

    current_time = datetime.now(timezone.utc)
    expiry_datetime = datetime.fromtimestamp(expiry, tz=timezone.utc)
    return current_time > expiry_datetime

class GogIntegration(StoreIntegrationProtocol):
    ACCESS_TOKEN_URL = "https://api.gog.com/user/accessToken.json"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.bearer_token = None

        # Prova a caricare i cookie
        if not load_cookies_into_session(self.session, COOKIE_FILE):
            print("🔄 Login necessario: avvio Selenium...")
            gog_auth = GogAuthSelenium(self.username, self.password)
            gog_auth.login()  # Esegue il login con Selenium e salva i cookie
            print("✅ Login completato! Riprovo a caricare i cookie...")
            load_cookies_into_session(self.session, COOKIE_FILE)  # Riprova a caricare i cookie

    def get_bearer_token(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Referer": "https://www.gog.com/"
        }
        """Effettua una richiesta per ottenere il Bearer Token usando i cookie salvati."""
        response = self.session.post(self.ACCESS_TOKEN_URL, headers=headers)

        if response.status_code == 200:
            token_data = response.json()
            print("✅ Bearer Token ricevuto:", token_data["accessToken"])
            return token_data["accessToken"]
        else:
            print("❌ Impossibile ottenere il Bearer Token.")
            print(response.text)
            return None

    def call_for_access_token(self):
        """Usa la sessione autenticata per ottenere il Bearer Token."""
        response = self.session.post(self.ACCESS_TOKEN_URL)

        if response.status_code == 200:
            token_data = response.json()
            print("✅ Bearer Token ricevuto:", token_data["accessToken"])
            return token_data["accessToken"]
        else:
            print("❌ Impossibile ottenere il Bearer Token.")
            print(response.text)
            return None

    def get_owned_games(self):
        url = f'https://menu.gog.com/v1/account/licences'
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
    
    def set_bearer_token(self, api_key):
        self.bearer_token = api_key

# Esempio di utilizzo
if __name__ == "__main__":
    username = GOG_USERNAME
    password = GOG_PASSWORD

    gog_api = GogIntegration(username, password)
    bearer_token = gog_api.get_bearer_token()
    gog_api.set_bearer_token(bearer_token)

    owned_games = gog_api.get_owned_games()
    print("🎮 Giochi posseduti su GOG:")
    for game in owned_games:
        game_info = gog_api.get_game_info(game['id'])
        print(game_info['title'])
        print("📅 Data di rilascio:", game_info['release_date'])

