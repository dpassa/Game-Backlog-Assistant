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