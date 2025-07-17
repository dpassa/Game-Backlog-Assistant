from dotenv import load_dotenv
import os

# Carica le variabili dal file .env
load_dotenv()

# Recupera le variabili
NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')
STEAM_API_KEY = os.getenv('STEAM_API_KEY')
STEAM_USERID_64 = os.getenv('STEAM_USERID_64')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
IGDB_CLIENT_ID = os.getenv('IGDB_CLIENTID')
IGDB_SECRET = os.getenv('IGDB_SECRET')
GOG_USERNAME = "BifcottoLol"


GOG_PROFILE_URL = "https://www.gog.com/u/BifcottoLol/games?"

IGDB_API_V4 = "https://api.igdb.com/v4"
IGDB_API_V4_GENRES = IGDB_API_V4 + '/genres'
IGDB_API_V4_THEMES = IGDB_API_V4 + '/themes'
IGDB_API_V4_PLATFORMS = IGDB_API_V4 + '/platforms'
IGDB_API_V4_GAMES = IGDB_API_V4 + '/games'
IGDB_API_V4_GAME_MODES = IGDB_API_V4 + '/game_modes'
IGDB_API_V4_WEBSITES = IGDB_API_V4 + '/websites'
IGDB_API_V4_COVERS = IGDB_API_V4 + '/covers'