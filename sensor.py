import logging
from datetime import timedelta, datetime
import requests

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=10)
_LOGGER = logging.getLogger(__name__)

class PrinterAPI:
    """Classe pour gérer l'API de l'imprimante."""
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
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
        async_add_entities(StateSensor(coordinator, printer) for printer in coordinator.data)
        async_add_entities(CurrentLayerSensor(coordinator, printer) for printer in coordinator.data)
        async_add_entities(CurrentPrintRunSensor(coordinator, printer) for printer in coordinator.data)
        async_add_entities(FirmwareSensor(coordinator, printer) for printer in coordinator.data)
        async_add_entities(CartridgeSensor(coordinator, printer) for printer in coordinator.data)
        # async_add_entities(BackCartridgeSensor(coordinator, printer) for printer in coordinator.data)
        


class StateSensor(CoordinatorEntity, SensorEntity):
    """Capteur pour suivre l'état d'une imprimante Form4."""

    def __init__(self, coordinator, printer_data):
        """Initialise une imprimante spécifique."""
        super().__init__(coordinator)
        self.printer_data = printer_data
        self._attr_name = f"Etat"
        self._attr_unique_id = f"{printer_data['machine_type_id']}_{printer_data['serial']}_state"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, printer_data["serial"])},
            name=printer_data["serial"],
            manufacturer="Formlabs",
            model="Form 4",
        )

    @property
    def state(self):
        return self.printer_data["printer_status"]["status"]

    @property
    def extra_state_attributes(self):
        return {key: value for key, value in self.printer_data["printer_status"].items() if key not in ["status", "current_print_run"]}

class CurrentLayerSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, printer_data):
        super().__init__(coordinator)
        self.printer_data = printer_data
        self._attr_name = f"Couche"
        self._attr_unique_id = f"{printer_data['machine_type_id']}_{printer_data['serial']}_current_layer"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, printer_data["serial"])},
            name=printer_data["serial"],
            manufacturer="Formlabs",
            model="Form 4",
        )

    @property
    def state(self):

        if self.printer_data["printer_status"]["current_print_run"] != None:
            current_layer = self.printer_data["printer_status"]["current_print_run"]["currently_printing_layer"]
            return f"{current_layer}"
        else:
            return "N/A"

    @property
    def extra_state_attributes(self):
        return {
        }

class CurrentPrintRunSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, printer_data):
        super().__init__(coordinator)
        self.printer_data = printer_data
        self._attr_name = f"Statut de l'impression"
        self._attr_unique_id = f"{printer_data['machine_type_id']}_{printer_data['serial']}_current_print"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, printer_data["serial"])},
            name=printer_data["serial"],
            manufacturer="Formlabs",
            model="Form 4",
        )

    @property
    def state(self):

        if self.printer_data["printer_status"]["current_print_run"] != None:
            return "En cours"
        return "N/A"

    @property
    def extra_state_attributes(self):
        if self.printer_data["printer_status"]["current_print_run"] != None:
            return {key: value for key, value in self.printer_data["printer_status"]["current_print_run"].items()}
        else:
            return {}

class CartridgeSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, printer_data):
        super().__init__(coordinator)
        self.printer_data = printer_data
        self._attr_name = f"Cartouches"
        self._attr_unique_id = f"{printer_data['machine_type_id']}_{printer_data['serial']}_front_cartridge"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, printer_data["serial"])},
            name=printer_data["serial"],
            manufacturer="Formlabs",
            model="Form 4",
        )

    @property
    def state(self):
        return ""
        

    @property
    def extra_state_attributes(self):
        cartridge_status = self.printer_data["cartridge_status"]
        if isinstance(cartridge_status, dict):
            return {key: value for key, value in cartridge_status.items()}
        elif isinstance(cartridge_status, list):
            if len(cartridge_status) == 2:
                return {
                    "front_cartridge": cartridge_status[0],
                    "back_cartridge": cartridge_status[1]
                }
            else:
                return {"cartridge_status": cartridge_status}
        else:
            return {}


# class BackCartridgeSensor(CoordinatorEntity, SensorEntity):
#     def __init__(self, coordinator, printer_data):
#         super().__init__(coordinator)
#         self.printer_data = printer_data
#         self._attr_name = f"Cartouche arrière"
#         self._attr_unique_id = f"{printer_data['machine_type_id']}_{printer_data['serial']}_back_cartridge"
#         self._attr_device_info = DeviceInfo(
#             identifiers={(DOMAIN, printer_data["serial"])},
#             name=printer_data["serial"],
#             manufacturer="Formlabs",
#             model="Form 4",
#         )

#     @property
#     def state(self):

#         if self.printer_data["cartridge_status"].length > 0:
#             for cartridge in self.printer_data["cartridge_status"]:
#                 if cartridge["cartridge_slot"] == "Back":
#                     return cartridge["cartridge"]["material"]
#         else :
#             return "N/A"


#     @property
#     def extra_state_attributes(self):
#         if self.printer_data["cartridge_status"].length > 0:
#             for cartridge in self.printer_data["cartridge_status"]:
#                 if cartridge["cartridge_slot"] == "FRONT":
#                     return {key: value for key, value in cartridge["cartridge"].items()}
#         else :
#             if self.printer_data["cartridge_status"].length == 1:
#                 return {key: value for key, value in self.printer_data["cartridge_status"][0].items()}
#             else:
#                 return "N/A"
        
class FirmwareSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, printer_data):
        super().__init__(coordinator)
        self.printer_data = printer_data
        self._attr_name = f"Firmware"
        self._attr_unique_id = f"{printer_data['machine_type_id']}_{printer_data['serial']}_firmware"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, printer_data["serial"])},
            name=printer_data["serial"],
            manufacturer="Formlabs",
            model="Form 4",
        )

    @property
    def state(self):
        return self.printer_data["firmware_version"]

    @property
    def extra_state_attributes(self):
        return {}