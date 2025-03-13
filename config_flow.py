import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class Form4ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="Formlabs Printers", data=user_input)

        data_schema = vol.Schema({
            vol.Required("client_id"): str,
            vol.Required("client_secret"): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
