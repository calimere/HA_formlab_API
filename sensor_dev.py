import logging
import requests
from datetime import timedelta
from datetime import datetime
import time
import asyncio

CLIENT_ID = "7MPpF5MwR6SFFYBbsisKuGiWrkWAlGGaJrVPnvYG"
CLIENT_SECRET = "0ns5XlCGIwWnVQvAqTtpU8nN89xCi5UOoy9EvkRZLzGsFeIIJAhx37OCo0Q0qWWlPhZ3dbCWllbPSVhjggehrnhiYwWeic37fx6PIMKRsIe6Z7Mwk2H4U7M64W3zv8mg"
AUTH_URL = "https://api.formlabs.com/developer/v1/o/token/"
GET_URL = "https://api.formlabs.com/developer/v1/printers/"
SCAN_INTERVAL = timedelta(seconds=10)  # Pour le test, on utilise un intervalle court

TOKEN = ""
EXPIRES = 0
AUTH_TIME = datetime.now()

# Paramètres de log pour le debug
logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

def auth_printer():
    global TOKEN
    global EXPIRES

    headers = { "content-type": "application/x-www-form-urlencoded" }
    data = { "grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET }
    response = requests.post(AUTH_URL, headers=headers, data=data)
    
    if response.status_code == 200:
        json_data = response.json()

        TOKEN = json_data.get("access_token")
        EXPIRES = json_data.get("expires_in")
    else:
        print("Échec de la requête:", response.status_code, response.text)

# Fonction simulée pour obtenir des données de l'API
def get_printer_data():
    try:

        headers = {"content-type": "application/x-www-form-urlencoded","Authorization": "Bearer " + TOKEN }
        response = requests.get(GET_URL, headers=headers)

        if response.status_code == 200:
            print(response.json())
            return response.json()
        else:
            print("Échec de la requête:", response.status_code, response.text)

    except requests.exceptions.RequestException as e:
        _LOGGER.error(f"Erreur de requête: {e}")
        return None

# Classe modifiée pour tester sans Home Assistant
class Form4PrinterSensor:
    def __init__(self):
        self._name = "Formlabs Printer"
        self._state = None
        self._attributes = {}

    def update(self):

        data = get_printer_data()

        print({key: value for key, value in data[0]["printer_status"].items() if key not in ["status", "current_print_run"]})

        if data:
            self._state = data[0]["printer_status"]["status"]
            self._attributes = {
                "serial": data[0]["serial"],
                "alias": data[0]["alias"],
                "material": data[0]["current_print_run"]["material"],
                "volume_ml": data[0]["current_print_run"]["volume_ml"],
                "layer_count": data[0]["current_print_run"]["layer_count"],
                "current_temperature": data[0]["printer_status"]["current_temperature"],
                "user": data[0]["current_print_run"]["user"]["username"]
            }
            self.display_state()

    def display_state(self):
        """Affiche l'état actuel et les attributs du capteur."""
        print(f"\nCapteur: {self._name}")
        print(f"État: {self._state}")
        print("Attributs:")
        for key, value in self._attributes.items():
            print(f"  - {key}: {value}")


async def main():

    sensor = Form4PrinterSensor()
    while True:

        print("TOKEN : " + TOKEN)
        if TOKEN != "":
            if datetime.now() <= (AUTH_TIME + timedelta(milliseconds=(EXPIRES - 6000))):
                sensor.update()
            else:
                auth_printer()
        else:
            auth_printer()
    
        await asyncio.sleep(SCAN_INTERVAL.total_seconds())

# Exécution du test
asyncio.run(main())
