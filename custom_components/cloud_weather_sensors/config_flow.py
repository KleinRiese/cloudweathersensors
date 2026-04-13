
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_REFRESH_TOKEN,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)
from .netatmo_api import NetatmoApiClient, NetatmoAuthError, NetatmoCommError

_LOGGER = logging.getLogger(__name__)


async def _validate_input(data: dict[str, Any]) -> None:
    api = NetatmoApiClient(
        client_id=data[CONF_CLIENT_ID],
        client_secret=data[CONF_CLIENT_SECRET],
        refresh_token=data[CONF_REFRESH_TOKEN],
    )
    await api.async_get_stations_data()


class NetatmoFavoritesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._reauth_entry = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            try:
                await _validate_input(user_input)
            except NetatmoAuthError:
                errors["base"] = "auth"
            except NetatmoCommError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="Cloud Weather Sensors", data=user_input)

        return self.async_show_form(step_id="user", data_schema=self._build_schema(), errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await _validate_input(user_input)
            except NetatmoAuthError:
                errors["base"] = "auth"
            except NetatmoCommError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during reauth")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    self._reauth_entry,
                    data_updates=user_input,
                    reason="reauth_successful",
                )

        defaults = self._reauth_entry.data if self._reauth_entry else {}
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self._build_schema(defaults),
            errors=errors,
        )

    def _build_schema(self, defaults: dict[str, Any] | None = None):
        defaults = defaults or {}
        return vol.Schema({
            vol.Required(CONF_CLIENT_ID, default=defaults.get(CONF_CLIENT_ID, "")): str,
            vol.Required(CONF_CLIENT_SECRET, default=defaults.get(CONF_CLIENT_SECRET, "")): str,
            vol.Required(CONF_REFRESH_TOKEN, default=defaults.get(CONF_REFRESH_TOKEN, "")): str,
        })

    @staticmethod
    def async_get_options_flow(config_entry):
        return NetatmoFavoritesOptionsFlowHandler(config_entry)


class NetatmoFavoritesOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        scan = int(self.entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        schema = vol.Schema({
            vol.Required(CONF_SCAN_INTERVAL, default=scan): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600))
        })
        return self.async_show_form(step_id="init", data_schema=schema)
