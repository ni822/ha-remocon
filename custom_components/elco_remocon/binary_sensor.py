"""Binary sensor entities for Elco Remocon-Net."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import RemoconData
from .const import DOMAIN
from .coordinator import ElcoRemoconCoordinator


@dataclass(kw_only=True)
class ElcoBinarySensorDescription(BinarySensorEntityDescription):
    """Describe an Elco binary sensor entity."""

    key: str
    translation_key: str
    device_class: BinarySensorDeviceClass | None = None
    value_fn: Callable[[RemoconData], bool]
    exists_fn: Callable[[RemoconData], bool] = lambda _: True
    plant_level: bool = False  # whole-plant value: created once per gateway


BINARY_SENSORS: tuple[ElcoBinarySensorDescription, ...] = (
    ElcoBinarySensorDescription(
        key="heating_active",
        translation_key="heating_active",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda d: d.heating_active,
    ),
    ElcoBinarySensorDescription(
        key="cooling_active",
        translation_key="cooling_active",
        device_class=BinarySensorDeviceClass.COLD,
        value_fn=lambda d: d.cooling_active,
        exists_fn=lambda d: not d.is_boiler,
    ),
    ElcoBinarySensorDescription(
        key="heat_pump_on",
        plant_level=True,
        translation_key="heat_pump_on",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.heat_pump_on,
        exists_fn=lambda d: not d.is_boiler,
    ),
    ElcoBinarySensorDescription(
        key="burner_on",
        plant_level=True,
        translation_key="burner_on",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.burner_on,
        exists_fn=lambda d: d.is_boiler,
    ),
    ElcoBinarySensorDescription(
        key="dhw_enabled",
        plant_level=True,
        translation_key="dhw_enabled",
        value_fn=lambda d: d.dhw_enabled,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Elco binary sensors."""
    coordinator: ElcoRemoconCoordinator = hass.data[DOMAIN][entry.entry_id]
    gw_id = coordinator.uid_prefix

    entities = [
        ElcoBinarySensor(coordinator, gw_id, desc)
        for desc in BINARY_SENSORS
        if desc.exists_fn(coordinator.data) and (coordinator.is_primary or not desc.plant_level)
    ]
    async_add_entities(entities)


class ElcoBinarySensor(CoordinatorEntity[ElcoRemoconCoordinator], BinarySensorEntity):
    """Elco binary sensor entity."""

    _attr_has_entity_name = True
    entity_description: ElcoBinarySensorDescription

    def __init__(
        self,
        coordinator: ElcoRemoconCoordinator,
        gw_id: str,
        description: ElcoBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{gw_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.entity_description.value_fn(self.coordinator.data)
