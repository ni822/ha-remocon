"""Number entity to set how often the Remocon-Net cloud is polled."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_MIN,
    DOMAIN,
    MAX_SCAN_INTERVAL_MIN,
    MIN_SCAN_INTERVAL_MIN,
)
from .coordinator import ElcoRemoconCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: ElcoRemoconCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ElcoUpdateIntervalNumber(coordinator, entry)])


class ElcoUpdateIntervalNumber(CoordinatorEntity[ElcoRemoconCoordinator], NumberEntity):
    """Polling interval in minutes, editable directly from the UI."""

    _attr_has_entity_name = True
    _attr_translation_key = "update_interval"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:timer-cog-outline"
    _attr_native_min_value = MIN_SCAN_INTERVAL_MIN
    _attr_native_max_value = MAX_SCAN_INTERVAL_MIN
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, coordinator: ElcoRemoconCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{coordinator.gateway_id}_update_interval"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        minutes = self._entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MIN)
        return max(MIN_SCAN_INTERVAL_MIN, min(MAX_SCAN_INTERVAL_MIN, int(minutes)))

    async def async_set_native_value(self, value: float) -> None:
        minutes = max(MIN_SCAN_INTERVAL_MIN, min(MAX_SCAN_INTERVAL_MIN, int(value)))
        # Saving the option reloads the entry (see __init__), which applies the new interval.
        self.hass.config_entries.async_update_entry(
            self._entry, options={**self._entry.options, CONF_SCAN_INTERVAL: minutes}
        )
