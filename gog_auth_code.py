import requests
import json
from consts import GOG_USERNAME

class GogAuthCode:
    BASE_AUTH_URL = "https://login.gog.com"

    def __init__(self):
        self.username = GOG_USERNAME
        self.password = "GOG_PASSWORD"
        self.access_token = None
        self.session = requests.Session()

        # Aggiungi i cookie alla sessione
        self.session.cookies.set('gog_lc', 'IT_EUR_en-US', domain='.gog.com', path='/')
        self.session.cookies.set('cart_token', 'glogloglogloglog', domain='.gog.com', path='/') #sample 1749cc303443c939
        self.session.cookies.set('galaxy-login-s', 'p83nbpdfkurge5m5b7s5h7avj0', domain='.gog.com', path='/') #sample p83nbpdfkurge5m5b7s5h7avj0

    def login(self):
        body = {
            "login[username]": self.username,
            "login[password]": self.password,
            "login[login_flow]": "default",
            "login[_token]": "????"  # Sample QZo6pdgLu_Yu9_BMxU5OG1t5nwOBFY_BPcQL7Aqhc2U
        }

        response = self.session.post(self.BASE_AUTH_URL + "/login_check", data=body)

        if response.status_code >= 200 and response.status_code < 300:
            token_data = response.json()
            self.access_token = token_data['access_token']
            print("✅ Login effettuato con successo!")
            print("Access Token:", self.access_token)
            return self.access_token
        elif response.status_code >= 300 and response.status_code < 400:
            response = self.two_step_auth()
            print("✅ Login effettuato con successo!")
            print("Access Token:", self.access_token)
            return self.access_token
        else:
            print("❌ Errore nel login:", response.text)
            return None
        
    def two_step_auth(self):
        # Richiede il codice di autenticazione a due fattori (2FA)
        print("ℹ️ Richiesto codice di autenticazione a due fattori.")
        # la stringa deve essere di 4 caratteri di tutti numeri
        two_step_auth_code = input("Inserisci il codice di autenticazione a due fattori: ")
        # La stringa deve essere divisa in 4 singoli caratteri
        # Esempio: "1234" -> ["1", "2", "3", "4"]
        # two_step_auth_code = list(two_step_auth_code)

        body = {
            "second_step_authentication[token][letter_1]": two_step_auth_code,
            "second_step_authentication[token][letter_2]": two_step_auth_code,
            "second_step_authentication[token][letter_3]": two_step_auth_code,
            "second_step_authentication[token][letter_4]": two_step_auth_code,
            "second_step_authentication[_token]": "zvbCxFSbtrDBCheam7_AiphtyOVWLPMMMKn1v9gFmtI" # Sample zvbCxFSbtrDBCheam7_AiphtyOVWLPMMMKn1v9gFmtI
        }

        response = self.session.post(self.BASE_AUTH_URL + "/login_check", data=body)

    

    def save_token(self, token_file="gog_token.json"):
        if self.access_token:
            with open(token_file, "w") as f:
                json.dump({"access_token": self.access_token}, f)
            print(f"✅ Access Token salvato in {token_file}")
        else:
            print("❌ Nessun Access Token da salvare.")

# Esempio di utilizzo
if __name__ == "__main__":
    gog_auth = GogAuthCode()
    access_token = gog_auth.login()
    if access_token:
        gog_auth.save_token()