"""Elco Remocon-Net integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .api import RemoconClient
from .const import CONF_GATEWAY_ID, CONF_ZONE, DOMAIN
from .coordinator import ElcoRemoconCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.WATER_HEATER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Elco Remocon-Net from a config entry."""
    coordinator = ElcoRemoconCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    _remove_obsolete_entities(hass, entry)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Reload when options (polling interval) change
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


def _remove_obsolete_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Drop entities from earlier versions that no longer exist (room temperature sensor, holiday mode)."""
    gw = entry.data[CONF_GATEWAY_ID]
    registry = er.async_get(hass)
    for domain, unique_id in (
        ("sensor", f"{gw}_room_temp"),
        ("date", f"{gw}_holiday_until"),
        ("button", f"{gw}_button_cancel_holiday"),
        ("button", f"{gw}_button_mode_holiday"),
        ("binary_sensor", f"{gw}_holiday_active"),
        ("number", f"{gw}_holiday_duration"),
    ):
        entity_id = registry.async_get_entity_id(domain, DOMAIN, unique_id)
        if entity_id:
            registry.async_remove(entity_id)


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry so the new polling interval applies."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
