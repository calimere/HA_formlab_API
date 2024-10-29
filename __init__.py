import logging
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "form4"

async def async_setup(hass: HomeAssistant, config: dict):
    _LOGGER.info("Setting up Form4 integration")
    return True