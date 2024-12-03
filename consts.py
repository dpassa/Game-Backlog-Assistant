from dotenv import load_dotenv
import os

# Carica le variabili dal file .env
load_dotenv()

# Recupera le variabili
NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')