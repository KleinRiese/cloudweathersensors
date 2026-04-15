
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


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

    @property
    def has_access_token(self) -> bool:
        return self._access_token is not None

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
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise NetatmoCommError(err) from err

        if resp.status in (400, 401, 403):
            raise NetatmoAuthError(payload)
        if resp.status >= 500:
            raise NetatmoCommError(payload)
        if resp.status >= 400:
            raise NetatmoCommError(payload)

        access = payload.get("access_token")
        refresh = payload.get("refresh_token")
        if not access or not refresh:
            raise NetatmoAuthError(payload)

        self._access_token = access
        self._refresh_token = refresh
        _LOGGER.debug("Netatmo token refresh successful; access and refresh token updated")
        return NetatmoTokens(access_token=access, refresh_token=refresh)

    async def _async_api_get(self, session: aiohttp.ClientSession, url: str, headers: dict[str, str]) -> tuple[int, dict[str, Any]]:
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                payload = await resp.json(content_type=None)
                return resp.status, payload
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise NetatmoCommError(err) from err

    async def _async_refresh_and_retry(self, session: aiohttp.ClientSession, url: str) -> dict[str, Any]:
        _LOGGER.warning("Refreshing Netatmo access token and retrying request")
        await self._async_refresh_access_token()
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }
        status, payload = await self._async_api_get(session, url, headers)

        if status in (400, 401, 403):
            raise NetatmoAuthError(payload)
        if status >= 500:
            raise NetatmoCommError(payload)
        if status >= 400:
            raise NetatmoCommError(payload)

        error = payload.get("error") or {}
        if isinstance(error, dict) and error.get("code") == 3:
            raise NetatmoAuthError(payload)
        if payload.get("status") != "ok":
            raise NetatmoCommError(payload)
        return payload

    async def async_get_stations_data(self) -> dict[str, Any]:
        url = "https://api.netatmo.com/api/getstationsdata?get_favorites=true"

        if not self._access_token:
            _LOGGER.debug("No cached access token available, requesting one via refresh token")
            await self._async_refresh_access_token()

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }

        async with aiohttp.ClientSession() as session:
            status, payload = await self._async_api_get(session, url, headers)

            error = payload.get("error") or {}
            error_code = error.get("code") if isinstance(error, dict) else None

            if status == 401 or error_code == 3:
                _LOGGER.warning(
                    "Netatmo token appears expired (http_status=%s, error_code=%s), trying refresh flow",
                    status,
                    error_code,
                )
                return await self._async_refresh_and_retry(session, url)

            if status in (400, 403):
                raise NetatmoAuthError(payload)
            if status >= 500:
                raise NetatmoCommError(payload)
            if status >= 400:
                raise NetatmoCommError(payload)

        if payload.get("status") != "ok":
            if error_code in (2, 3):
                raise NetatmoAuthError(payload)
            raise NetatmoCommError(payload)

        return payload
