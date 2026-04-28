"""Data update coordinator for NPMplus."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NPMplusApiClient, NPMplusAuthError, NPMplusConnectionError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class NPMplusCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator for polling NPMplus proxy hosts."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._entry = entry
        self.api = NPMplusApiClient(
            base_url=entry.data[CONF_URL],
            identity=entry.data[CONF_USERNAME],
            secret=entry.data[CONF_PASSWORD],
            verify_ssl=entry.data.get(CONF_VERIFY_SSL, False),
        )

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch proxy hosts from NPMplus."""
        try:
            return await self.api.async_get_proxy_hosts()
        except NPMplusAuthError as err:
            raise ConfigEntryAuthFailed from err
        except NPMplusConnectionError as err:
            # Force a fresh session on next poll to recover from stuck connector
            # state (stale DNS, dead sockets, lingering TimeoutError after server
            # restart) that aiohttp's pool eviction may not detect.
            await self.api.async_close()
            raise UpdateFailed(f"Cannot connect to NPMplus: {err}") from err

    async def async_shutdown(self) -> None:
        """Close the API session on shutdown."""
        await super().async_shutdown()
        await self.api.async_close()
