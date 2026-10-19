"""Domestic hot water (DHW) entity for Elco Remocon-Net."""

from __future__ import annotations

import re

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import RemoconData
from .const import DOMAIN
from .coordinator import ElcoRemoconCoordinator

FALLBACK_MODES = {"off": 0, "on": 1}


def _slug(text: str, value: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or f"mode_{value}"


def _mode_map(data: RemoconData) -> dict[str, int]:
    """Operation name -> API value, built from what the system allows."""
    if not data.dhw_mode_options:
        return dict(FALLBACK_MODES)
    return {_slug(text, value): value for value, text in data.dhw_mode_options}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: ElcoRemoconCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.is_primary and coordinator.data.has_dhw:
        async_add_entities([ElcoWaterHeater(coordinator)])


class ElcoWaterHeater(CoordinatorEntity[ElcoRemoconCoordinator], WaterHeaterEntity):
    """Domestic hot water boiler."""

    _attr_has_entity_name = True
    _attr_translation_key = "dhw"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
    )

    def __init__(self, coordinator: ElcoRemoconCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.uid_prefix}_dhw"
        self._attr_device_info = coordinator.device_info

    @property
    def current_temperature(self) -> float | None:
        t = self.coordinator.data.dhw_temp
        return t if t > 0 else None

    @property
    def target_temperature(self) -> float | None:
        t = self.coordinator.data.dhw_comfort_temp
        return t if t > 0 else None

    @property
    def target_temperature_step(self) -> float:
        return self.coordinator.data.dhw_comfort_temp_step

    @property
    def min_temp(self) -> float:
        return self.coordinator.data.dhw_comfort_temp_min

    @property
    def max_temp(self) -> float:
        return self.coordinator.data.dhw_comfort_temp_max

    @property
    def operation_list(self) -> list[str]:
        return list(_mode_map(self.coordinator.data))

    @property
    def current_operation(self) -> str | None:
        data = self.coordinator.data
        for name, value in _mode_map(data).items():
            if value == data.dhw_mode:
                return name
        return None

    async def async_set_temperature(self, **kwargs) -> None:
        temperature = kwargs.get("temperature")
        if temperature is None:
            return
        await self.hass.async_add_executor_job(
            self.coordinator.client.set_dhw_temperature, float(temperature), None
        )
        await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        value = _mode_map(self.coordinator.data).get(operation_mode)
        if value is None:
            return
        await self.hass.async_add_executor_job(self.coordinator.client.set_dhw_mode, value)
        await self.coordinator.async_request_refresh()
