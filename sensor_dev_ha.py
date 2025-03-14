import logging
from datetime import timedelta, datetime
import requests

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

SCAN_INTERVAL = timedelta(seconds=10)
_LOGGER = logging.getLogger(__name__)

class PrinterAPI:
    """Classe pour gérer l'API de l'imprimante."""
    def __init__(self, client_id, client_secret):
        self.client_id = "7MPpF5MwR6SFFYBbsisKuGiWrkWAlGGaJrVPnvYG"
        self.client_secret = "0ns5XlCGIwWnVQvAqTtpU8nN89xCi5UOoy9EvkRZLzGsFeIIJAhx37OCo0Q0qWWlPhZ3dbCWllbPSVhjggehrnhiYwWeic37fx6PIMKRsIe6Z7Mwk2H4U7M64W3zv8mg"
        self.token = None
        self.token_expiry = None

    def authenticate(self):
        """Récupère un token d'authentification."""
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "client_credentials", "client_id": self.client_id, "client_secret": self.client_secret}
        
        response = requests.post("https://api.formlabs.com/developer/v1/o/token/", headers=headers, data=data)
        
        if response.status_code == 200:
            json_data = response.json()
            self.token = json_data.get("access_token")
            self.token_expiry = datetime.now() + timedelta(seconds=json_data.get("expires_in", 3600) - 60)
        else:
            _LOGGER.error("Échec de l'authentification: %s", response.text)

    def get_printer_data(self):
        """Récupère les données de toutes les imprimantes."""
        if not self.token or datetime.now() >= self.token_expiry:
            self.authenticate()

        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get("https://api.formlabs.com/developer/v1/printers/", headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            _LOGGER.error("Échec de la récupération des données des imprimantes: %s", response.text)
            return None

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Configurer plusieurs imprimantes via une entrée de configuration."""
    client_id = entry.data["client_id"]
    client_secret = entry.data["client_secret"]

    api = PrinterAPI(client_id, client_secret)

    async def async_update_data():
        """Met à jour les données de toutes les imprimantes."""
        return await hass.async_add_executor_job(api.get_printer_data)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="formlabs_printers",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    if coordinator.data:
        async_add_entities(Form4PrinterSensor(coordinator, printer) for printer in coordinator.data)

class Form4PrinterSensor(CoordinatorEntity, SensorEntity):
    """Capteur pour suivre l'état d'une imprimante Form4."""

    def __init__(self, coordinator, printer_data):
        """Initialise une imprimante spécifique."""
        super().__init__(coordinator)
        self.printer_data = printer_data
        self._attr_name = f"Form4 {printer_data['alias']}"
        self._attr_unique_id = printer_data["serial"]
        self._attr_device_info = DeviceInfo(
            identifiers={("formlab", printer_data["serial"])},
            name=printer_data["alias"],
            manufacturer="Formlabs",
            model="Form 4",
        )

    @property
    def state(self):
        """Retourne l'état actuel de l'imprimante."""
        return self.printer_data["printer_status"]["status"]

    @property
    def extra_state_attributes(self):
        """Retourne des attributs supplémentaires."""
        return {
            "serial": self.printer_data["serial"],
            "alias": self.printer_data["alias"],
            "current_temperature": self.printer_data["printer_status"]["current_temperature"],
        }
