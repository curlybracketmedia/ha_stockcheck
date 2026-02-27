from datetime import datetime, timedelta, timezone

class StockCheckSensor:
    """Represents a stock entity."""

    def __init__(self, hass, data):
        self.hass = hass
        self._data = data  # dict containing expiry, quantity, unit
        self._attr_name = data.get("name", "Unnamed Stock")
        self._attr_unique_id = data.get("name", "stock").lower().replace(" ", "_")
        self._state = None

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {
            "expiry": self._data.get("expiry"),
            "quantity": self._data.get("quantity"),
            "unit": self._data.get("unit"),
            "status": self._data.get("status"),
        }

    async def async_set_value(self, field, value):
        """Update a single field."""
        self._data[field] = value
        if field in ["expiry"]:
            self._data["status"] = self.calculate_status(self._data.get("expiry"))
        self.async_write_ha_state()

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

    @callback
    def async_write_ha_state(self):
        """Notify HA that the entity state changed."""
        # This needs to hook into the actual HA Entity object in sensor.py
        # If using EntityComponent, call self.entity.async_write_ha_state()
        pass
