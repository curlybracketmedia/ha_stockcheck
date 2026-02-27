from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Stock Checks from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("entities", {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward setup to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    async def async_set_value(call: ServiceCall):
        """Handle attribute updates."""
        entity_id = call.data.get("entity_id")
        _, _, field = call.service.partition("set_")
        value = call.data.get("value")

        entity = hass.data[DOMAIN]["entities"].get(entity_id)
        if entity:
            await entity.async_set_value(field, value)

    # Register services
    for field in ["expiry", "quantity", "unit"]:
        hass.services.async_register(DOMAIN, f"set_{field}", async_set_value)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
