
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.diagnostics import async_redact_data

from .const import DOMAIN, CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_REFRESH_TOKEN

TO_REDACT = {CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_REFRESH_TOKEN, "access_token", "mail", "location"}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "data": async_redact_data(coordinator.data, TO_REDACT),
    }
