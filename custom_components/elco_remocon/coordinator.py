"""DataUpdateCoordinator for Elco Remocon-Net."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
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
        self.client = RemoconClient(
            email=config_entry.data[CONF_EMAIL],
            password=config_entry.data[CONF_PASSWORD],
            gateway_id=config_entry.data[CONF_GATEWAY_ID],
            zone=config_entry.data.get(CONF_ZONE, "1"),
            system_type=config_entry.data.get(CONF_SYSTEM_TYPE, DEFAULT_SYSTEM_TYPE),
        )
        self.system_type: str = config_entry.data.get(CONF_SYSTEM_TYPE, DEFAULT_SYSTEM_TYPE)
        self.gateway_id: str = config_entry.data[CONF_GATEWAY_ID]

    @property
    def device_info(self) -> dict:
        """Shared device info for all entities of this gateway."""
        if self.system_type == SYSTEM_BOILER:
            name, model = "Remocon-Net Oil Boiler", "Oil boiler"
        else:
            name, model = "Remocon-Net Heat Pump", "Aerotop SPK"
        return {
            "identifiers": {(DOMAIN, self.gateway_id)},
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
