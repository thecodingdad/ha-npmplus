"""Base entity for NPMplus integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_URL
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import NPMplusCoordinator


class NPMplusEntity(CoordinatorEntity["NPMplusCoordinator"]):
    """Base entity for NPMplus."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: NPMplusCoordinator) -> None:
        """Initialize base entity."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator._entry.entry_id)},
            name="NPMplus",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=coordinator._entry.data[CONF_URL],
        )
