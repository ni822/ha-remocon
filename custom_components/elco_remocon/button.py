"""Button entities for Elco Remocon-Net: operating-mode presets and manual refresh."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MODE_AUTOMATIC,
    MODE_COMFORT,
    MODE_PROTECTION,
    MODE_REDUCTION,
)
from .coordinator import ElcoRemoconCoordinator


@dataclass(kw_only=True)
class ElcoButtonDescription(ButtonEntityDescription):
    """Describe an Elco button. ``mode`` None = manual refresh."""

    mode: int | None = None


BUTTONS: tuple[ElcoButtonDescription, ...] = (
    ElcoButtonDescription(key="refresh", translation_key="refresh", icon="mdi:cloud-refresh"),
    ElcoButtonDescription(key="mode_auto", translation_key="mode_auto",
                          icon="mdi:calendar-clock", mode=MODE_AUTOMATIC),
    ElcoButtonDescription(key="mode_comfort", translation_key="mode_comfort",
                          icon="mdi:white-balance-sunny", mode=MODE_COMFORT),
    ElcoButtonDescription(key="mode_reduced", translation_key="mode_reduced",
                          icon="mdi:weather-night", mode=MODE_REDUCTION),
    ElcoButtonDescription(key="mode_protection", translation_key="mode_protection",
                          icon="mdi:snowflake-alert", mode=MODE_PROTECTION),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: ElcoRemoconCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(ElcoButton(coordinator, desc) for desc in BUTTONS)


class ElcoButton(CoordinatorEntity[ElcoRemoconCoordinator], ButtonEntity):
    """Mode preset button or manual refresh button."""

    _attr_has_entity_name = True
    entity_description: ElcoButtonDescription

    def __init__(self, coordinator: ElcoRemoconCoordinator, description: ElcoButtonDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.gateway_id}_button_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def icon(self) -> str | None:
        """Mode buttons show which mode is currently active (radio-style icon)."""
        mode = self.entity_description.mode
        if mode is None:
            return self.entity_description.icon
        active = self.coordinator.data.zone_mode == mode
        return "mdi:radiobox-marked" if active else "mdi:radiobox-blank"

    async def async_press(self) -> None:
        mode = self.entity_description.mode
        if mode is None:
            # Fetch fresh data right now, regardless of the polling interval
            await self.coordinator.async_refresh()
            return
        await self.hass.async_add_executor_job(self.coordinator.client.set_zone_mode, mode)
        await self.coordinator.async_request_refresh()
