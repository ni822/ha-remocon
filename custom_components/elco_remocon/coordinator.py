"""DataUpdateCoordinator for Elco Remocon-Net."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_NAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RemoconAuthError, RemoconClient, RemoconConnectionError, RemoconData
from .const import (
    CONF_GATEWAY_ID,
    CONF_SCAN_INTERVAL,
    CONF_SYSTEM_TYPE,
    CONF_ZONE,
    DEFAULT_SCAN_INTERVAL_MIN,
    DEFAULT_SYSTEM_TYPE,
    DOMAIN,
    MAX_SCAN_INTERVAL_MIN,
    MIN_SCAN_INTERVAL_MIN,
    SYSTEM_BOILER,
    uid_prefix,
)

_LOGGER = logging.getLogger(__name__)


class ElcoRemoconCoordinator(DataUpdateCoordinator[RemoconData]):
    """Coordinator to poll Elco Remocon-Net data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        minutes = int(config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MIN))
        minutes = max(MIN_SCAN_INTERVAL_MIN, min(MAX_SCAN_INTERVAL_MIN, minutes))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=timedelta(minutes=minutes),
            always_update=False,
        )
        self.system_type: str = config_entry.data.get(CONF_SYSTEM_TYPE, DEFAULT_SYSTEM_TYPE)
        self.gateway_id: str = config_entry.data[CONF_GATEWAY_ID]
        self.zone: str = str(config_entry.data.get(CONF_ZONE, "1")).strip() or "1"
        self.uid_prefix: str = uid_prefix(self.gateway_id, self.zone)
        self._custom_name: str = (config_entry.data.get(CONF_NAME) or "").strip()
        # With several entries on one gateway (one per heating zone), the first one
        # created owns the plant-wide entities (outside temp, hot water, burner...).
        same_gateway = [
            e for e in hass.config_entries.async_entries(DOMAIN)
            if e.data.get(CONF_GATEWAY_ID) == self.gateway_id
        ]
        self.is_primary: bool = not same_gateway or same_gateway[0].entry_id == config_entry.entry_id
        self.client = RemoconClient(
            email=config_entry.data[CONF_EMAIL],
            password=config_entry.data[CONF_PASSWORD],
            gateway_id=self.gateway_id,
            zone=self.zone,
            system_type=self.system_type,
            fetch_plant_items=self.is_primary,
        )

    @property
    def device_info(self) -> dict:
        """Device shared by all entities of this entry (one device per heating zone)."""
        if self.system_type == SYSTEM_BOILER:
            name, model = "Remocon-Net Oil Boiler", "Oil boiler"
        else:
            name, model = "Remocon-Net Heat Pump", "Aerotop SPK"
        if self.zone != "1":
            name = f"{name} zone {self.zone}"
        if self._custom_name:
            name = self._custom_name
        return {
            "identifiers": {(DOMAIN, self.uid_prefix)},
            "name": name,
            "manufacturer": "Elco",
            "model": model,
        }

    async def _async_update_data(self) -> RemoconData:
        """Fetch data from the Remocon-Net cloud API."""
        try:
            return await self.hass.async_add_executor_job(self.client.get_data)
        except RemoconAuthError as err:
            raise ConfigEntryAuthFailed("Authentication failed") from err
        except RemoconConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
