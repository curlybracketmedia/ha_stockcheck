import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN


class StockCheckConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Stock."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input["name"], data=user_input)

        schema = vol.Schema({
            vol.Required("name", description={"name": "Name"}): str,
            vol.Required("quantity", default=100, description={"name": "Quantity"}): int,
            vol.Required("unit", default='kg', description={"name": "Unit"}): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema)
