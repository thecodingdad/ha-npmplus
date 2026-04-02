"""Config flow for NPMplus integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .api import NPMplusApiClient, NPMplusAuthError, NPMplusConnectionError
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_VERIFY_SSL, default=False): bool,
    }
)


class NPMplusConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NPMplus."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> NPMplusOptionsFlow:
        """Return the options flow handler."""
        return NPMplusOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            user_input[CONF_URL] = url

            client = NPMplusApiClient(
                base_url=url,
                identity=user_input[CONF_USERNAME],
                secret=user_input[CONF_PASSWORD],
                verify_ssl=user_input.get(CONF_VERIFY_SSL, False),
            )

            try:
                await client.async_authenticate()
                await client.async_get_proxy_hosts()
            except NPMplusConnectionError as err:
                _LOGGER.error("Cannot connect to NPMplus: %s", err)
                errors["base"] = "cannot_connect"
            except NPMplusAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during NPMplus setup")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"NPMplus ({url})",
                    data=user_input,
                )
            finally:
                await client.async_close()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class NPMplusOptionsFlow(OptionsFlow):
    """Handle NPMplus options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=current,
                    ): vol.All(
                        int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                    ),
                }
            ),
        )
