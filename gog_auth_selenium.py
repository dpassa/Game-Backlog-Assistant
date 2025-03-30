import json
import time
from consts import GOG_USERNAME, GOG_PASSWORD, LOGIN_URL, COOKIE_FILE
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

class GogAuthSelenium:

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.COOKIE_FILE = COOKIE_FILE
        self.LOGIN_URL = LOGIN_URL

        # Configura Chrome in modalità headless
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Esegue senza GUI
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=chrome_options)

    def login(self):
        """Effettua il login e salva i cookie su file."""
        self.driver.get(self.LOGIN_URL)

        try:
            # Accedi direttamente agli elementi email e password
            email_input = self.driver.find_element(By.NAME, "login[username]")
            password_input = self.driver.find_element(By.NAME, "login[password]")

            # Inserisci username e password
            email_input.send_keys(self.username)
            password_input.send_keys(self.password)
            password_input.send_keys(Keys.RETURN)

            time.sleep(3)
            self.driver.get("https://www.gog.com/")  # 🔥 Questo può attivare il set dei cookie

            # Attendi la conclusione del login
            time.sleep(5)

            # 🔹 Salva i cookie su file
            cookies = self.driver.get_cookies()
            with open(self.COOKIE_FILE, "w") as f:
                json.dump(cookies, f)

            print("✅ Login effettuato e cookie salvati in", self.COOKIE_FILE)

        except Exception as e:
            print("❌ Errore nel login:", e)

        finally:
            self.driver.quit()

# 🔥 **Esegui il login e salva i cookie**
if __name__ == "__main__":
    username = GOG_USERNAME
    password = GOG_PASSWORD

    gog_auth = GogAuthSelenium(username, password)
    gog_auth.login()
