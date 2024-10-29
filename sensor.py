import logging
import requests
from datetime import timedelta, datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.entity import async_generate_entity_id

CLIENT_ID = "7MPpF5MwR6SFFYBbsisKuGiWrkWAlGGaJrVPnvYG"
CLIENT_SECRET = "0ns5XlCGIwWnVQvAqTtpU8nN89xCi5UOoy9EvkRZLzGsFeIIJAhx37OCo0Q0qWWlPhZ3dbCWllbPSVhjggehrnhiYwWeic37fx6PIMKRsIe6Z7Mwk2H4U7M64W3zv8mg"
AUTH_URL = "https://api.formlabs.com/developer/v1/o/token/"
GET_URL = "https://api.formlabs.com/developer/v1/printers/"
SCAN_INTERVAL = timedelta(seconds=10)  # Pour le test, on utilise un intervalle court

TOKEN = ""
EXPIRES = 0
AUTH_TIME = datetime.now()

_LOGGER = logging.getLogger(__name__)

def auth_printer():
    global TOKEN
    global EXPIRES
    global AUTH_TIME

    headers = {"content-type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
    
    response = requests.post(AUTH_URL, headers=headers, data=data)
    
    if response.status_code == 200:
        json_data = response.json()
        TOKEN = json_data.get("access_token")
        EXPIRES = json_data.get("expires_in")
        AUTH_TIME = datetime.now()  # Met à jour le temps d'authentification
    else:
        _LOGGER.error("Échec de la requête d'authentification: %s", response.text)

def get_printer_data():
    try:
        headers = {"content-type": "application/x-www-form-urlencoded", "Authorization": "Bearer " + TOKEN}
        response = requests.get(GET_URL, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            _LOGGER.error("Échec de la requête de données d'imprimante: %s", response.text)

    except requests.exceptions.RequestException as e:
        _LOGGER.error("Erreur de requête: %s", e)
        return None

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    async_add_entities([Form4PrinterSensor(hass)], True)

class Form4PrinterSensor(SensorEntity):
    def __init__(self, hass):
        self.hass = hass
        self._name = "Form4 Printer"
        self._state = None
        self._attributes = {}
        self.entity_id = async_generate_entity_id('sensor.{}', self._name, hass=hass)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        # Vérifie si le token est vide ou s'il est expiré
        if not TOKEN or datetime.now() >= (AUTH_TIME + timedelta(seconds=EXPIRES - 60)):
            await self.hass.async_add_executor_job(auth_printer)  # Authentification asynchrone

        data = await self.hass.async_add_executor_job(get_printer_data)  # Appel de données asynchrone
        if data:
            self._state = data[0]["printer_status"]["status"]
            self._attributes = {
                "serial": data[0]["serial"],
                "alias": data[0]["alias"],
                "current_temperature": data[0]["printer_status"]["current_temperature"],
                "status": data[0]["printer_status"],
                # "material": data[0]["current_print_run"]["material"],
                # "volume_ml": data[0]["current_print_run"]["volume_ml"],
                # "layer_count": data[0]["current_print_run"]["layer_count"],
                # "user": data[0]["current_print_run"]["user"]["username"]
            }

    async def async_added_to_hass(self):
        self._unsub = async_track_time_interval(
            self.hass, self.async_update, SCAN_INTERVAL
        )
