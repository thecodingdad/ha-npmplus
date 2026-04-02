"""Switch platform for NPMplus proxy hosts."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import NPMplusCoordinator
from .entity import NPMplusEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NPMplus switch entities."""
    coordinator: NPMplusCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        NPMplusProxyHostSwitch(coordinator, host["id"])
        for host in coordinator.data
    ]
    async_add_entities(entities)


class NPMplusProxyHostSwitch(NPMplusEntity, SwitchEntity):
    """Switch to enable/disable an NPMplus proxy host."""

    _attr_icon = "mdi:server-network"

    def __init__(self, coordinator: NPMplusCoordinator, host_id: int) -> None:
        """Initialize the proxy host switch."""
        super().__init__(coordinator)
        self._host_id = host_id
        self._attr_unique_id = (
            f"{coordinator._entry.entry_id}_{host_id}"
        )
        host = self._get_host_data()
        if host:
            self._attr_name = host["domain_names"][0]

    def _get_host_data(self) -> dict[str, Any] | None:
        """Find this host in the coordinator data."""
        for host in self.coordinator.data:
            if host["id"] == self._host_id:
                return host
        return None

    @property
    def available(self) -> bool:
        """Return True if the host exists in coordinator data."""
        return super().available and self._get_host_data() is not None

    @property
    def is_on(self) -> bool | None:
        """Return True if the proxy host is enabled."""
        host = self._get_host_data()
        if host is None:
            return None
        return bool(host["enabled"])

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        host = self._get_host_data()
        if host is None:
            return None
        return {
            "domain_names": host["domain_names"],
            "forward_host": host["forward_host"],
            "forward_port": host["forward_port"],
            "forward_scheme": host.get("forward_scheme", "http"),
            "ssl_forced": host.get("ssl_forced", False),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the proxy host."""
        await self.coordinator.api.async_enable_proxy_host(self._host_id)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the proxy host."""
        await self.coordinator.api.async_disable_proxy_host(self._host_id)
        await self.coordinator.async_request_refresh()
