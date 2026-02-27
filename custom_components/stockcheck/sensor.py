from datetime import datetime, timedelta, timezone
import logging
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity  # <-- NEW import
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Home Assistant will poll this entity every minute
SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Stock Checks sensors from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("entities", {})

    stock = StockCheckSensor(hass, entry.data)
    async_add_entities([stock], True)

    # Store entity reference for service calls
    hass.data[DOMAIN]["entities"][stock.entity_id] = stock


class StockCheckSensor(RestoreEntity):
    """Representation of a single stock as a sensor."""

    def __init__(self, hass, data):
        self.hass = hass
        self._data = dict(data)
        self._attr_name = data.get("name", "Unnamed Stock")
        self._attr_unique_id = self._attr_name.lower().replace(" ", "_")
        self.entity_id = f"sensor.stockcheck_{self._attr_unique_id}"

        quantity = self._data.get("quantity", 100)
        self._data.setdefault("quantity", quantity)
        self._data.setdefault("unit", self._data.get("unit", 1))
        self._data.setdefault("expiry", None)

        self._data["status"] = self.calculate_status(self._data["expiry"])

    #
    # --- Restore state on restart ---
    #
    async def async_added_to_hass(self):
        """Restore previous state after Home Assistant restart."""
        await super().async_added_to_hass()

        old_state = await self.async_get_last_state()
        if old_state is not None:
            attrs = old_state.attributes
            self._data["expiry"] = attrs.get("expiry")
            self._data["status"] = old_state.state
            _LOGGER.debug(
                "Restored stock '%s' from previous state: %s",
                self._attr_name,
                old_state.state,
            )
        else:
            _LOGGER.debug(
                "No previous state found for '%s'; using defaults.", self._attr_name
            )

    #
    # --- Automatic polling / updating ---
    #
    @property
    def should_poll(self):
        """Tell HA to poll this entity every SCAN_INTERVAL."""
        return True

    async def async_update(self):
        """Called automatically by HA every SCAN_INTERVAL."""
        old_status = self._data.get("status")
        new_status = self.calculate_status(self._data.get("expiry"))

        if new_status != old_status:
            self._data["status"] = new_status
            _LOGGER.debug(
                "Stock '%s' status updated from '%s' to '%s'",
                self._attr_name,
                old_status,
                new_status,
            )
            self.async_write_ha_state()

    #
    # --- Standard sensor properties ---
    #
    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def state(self):
        return self._data.get("status", "Not Due")

    @property
    def extra_state_attributes(self):
        return {
            "expiry": self._data.get("expiry"),
            "quantity": self._data.get("quantity"),
            "unit": self._data.get("unit"),
        }

    async def async_set_value(self, field, value):
        """Update a single field on the stock."""
        if field in ["expiry"] and isinstance(value, str):
            try:
                datetime.fromisoformat(value)
                self._data[field] = value
            except Exception:
                _LOGGER.warning("Invalid date format for %s: %s", field, value)
        else:
            self._data[field] = value

        if field in ["expiry"]:
            self._data["status"] = self.calculate_status(self._data.get("expiry"))

        self.async_write_ha_state()

    #
    # --- Core status logic ---
    #
    def calculate_status(self, expiry_str):
        """Recalculate status based on expiry date."""
        if not expiry_str:
            return "Fine"

        now = datetime.now(timezone.utc)
        expiry = datetime.fromisoformat(expiry_str)
        delta = (expiry - now).total_seconds()

        if delta < -345600:
            return "Throw Out"
        elif delta < 0:
            return "Expired"
        elif delta < 345600:
            return "Expiring Soon"
        else:
            return "Fine"
