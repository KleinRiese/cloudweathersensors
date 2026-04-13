
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import aiohttp


class NetatmoCommError(Exception):
    pass


class NetatmoAuthError(Exception):
    pass


@dataclass
class NetatmoTokens:
    access_token: str
    refresh_token: str


class NetatmoApiClient:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._access_token: str | None = None

    @property
    def refresh_token(self) -> str:
        return self._refresh_token

    def update_credentials(self, client_id: str, client_secret: str, refresh_token: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._access_token = None

    async def _async_refresh_access_token(self) -> NetatmoTokens:
        url = "https://api.netatmo.com/oauth2/token"
        data = aiohttp.FormData()
        data.add_field("grant_type", "refresh_token")
        data.add_field("refresh_token", self._refresh_token)
        data.add_field("client_id", self._client_id)
        data.add_field("client_secret", self._client_secret)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    payload = await resp.json(content_type=None)
                    if resp.status >= 400:
                        raise NetatmoAuthError(payload)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise NetatmoCommError(err) from err

        access = payload.get("access_token")
        refresh = payload.get("refresh_token")
        if not access or not refresh:
            raise NetatmoAuthError(payload)

        self._access_token = access
        self._refresh_token = refresh
        return NetatmoTokens(access_token=access, refresh_token=refresh)

    async def async_get_stations_data(self) -> dict[str, Any]:
        if not self._access_token:
            await self._async_refresh_access_token()

        url = "https://api.netatmo.com/api/getstationsdata?get_favorites=true"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    payload = await resp.json(content_type=None)
                    if resp.status == 401:
                        await self._async_refresh_access_token()
                        headers["Authorization"] = f"Bearer {self._access_token}"
                        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp2:
                            payload = await resp2.json(content_type=None)
                            if resp2.status == 401:
                                raise NetatmoAuthError(payload)
                    elif resp.status >= 400:
                        raise NetatmoCommError(payload)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise NetatmoCommError(err) from err

        if payload.get("status") != "ok":
            raise NetatmoCommError(payload)

        return payload
