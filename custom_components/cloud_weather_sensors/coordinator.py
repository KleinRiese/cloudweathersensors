
from __future__ import annotations

import logging
from copy import deepcopy
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, CONF_REFRESH_TOKEN, CONF_SCAN_INTERVAL
from .netatmo_api import NetatmoApiClient, NetatmoAuthError, NetatmoCommError

_LOGGER = logging.getLogger(__name__)


class NetatmoFavoritesCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: NetatmoApiClient) -> None:
        self.api = api
        self.entry = entry
        scan = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name="Cloud Weather Sensors",
            config_entry=entry,
            update_interval=timedelta(seconds=scan),
            always_update=True,
        )

    async def _async_update_data(self) -> dict:
        try:
            data = await self.api.async_get_stations_data()
            await self._persist_refresh_token_if_changed()
            return self._normalize(data)
        except NetatmoAuthError as err:
            raise ConfigEntryAuthFailed(f"Netatmo auth error: {err}") from err
        except NetatmoCommError as err:
            raise UpdateFailed(f"Netatmo communication error: {err}") from err

    async def _persist_refresh_token_if_changed(self) -> None:
        current = self.entry.data.get(CONF_REFRESH_TOKEN)
        latest = self.api.refresh_token
        if not latest or latest == current:
            return

        new_data = dict(deepcopy(self.entry.data))
        new_data[CONF_REFRESH_TOKEN] = latest
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        self.entry = self.hass.config_entries.async_get_entry(self.entry.entry_id) or self.entry

    def _normalize(self, payload: dict) -> dict:
        body = payload.get("body") or {}
        devices = body.get("devices") or []
        stations = {}
        modules = {}
        for dev in devices:
            dev_id = dev.get("_id")
            if dev_id:
                stations[dev_id] = dev
            for mod in dev.get("modules") or []:
                mod_id = mod.get("_id")
                if mod_id:
                    modules[mod_id] = mod
        return {"raw": payload, "stations": stations, "modules": modules}
