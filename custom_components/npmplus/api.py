"""API client for NPMplus."""

from __future__ import annotations

import logging
import ssl
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class NPMplusConnectionError(Exception):
    """Error connecting to NPMplus."""


class NPMplusAuthError(Exception):
    """Authentication error with NPMplus."""


class NPMplusApiClient:
    """API client for NPMplus and Nginx Proxy Manager.

    Supports both cookie-based auth (NPMplus) and Bearer token auth
    (original NPM). Auto-detects which method the server uses.
    """

    def __init__(
        self,
        base_url: str,
        identity: str,
        secret: str,
        verify_ssl: bool = False,
    ) -> None:
        """Initialize the API client."""
        self._base_url = base_url.rstrip("/")
        self._identity = identity
        self._secret = secret
        self._verify_ssl = verify_ssl
        self._session: aiohttp.ClientSession | None = None
        self._authenticated = False
        self._token: str | None = None

    def _get_ssl_context(self) -> ssl.SSLContext | bool:
        """Return SSL context."""
        if not self._verify_ssl:
            return False
        return True

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Create or return the dedicated session with cookie jar."""
        if self._session is None or self._session.closed:
            jar = aiohttp.CookieJar(unsafe=True)
            self._session = aiohttp.ClientSession(cookie_jar=jar)
            self._authenticated = False
        return self._session

    async def async_close(self) -> None:
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            self._authenticated = False
            self._token = None

    async def async_authenticate(self) -> None:
        """Authenticate and store the session cookie."""
        session = await self._ensure_session()

        try:
            resp = await session.post(
                f"{self._base_url}/api/tokens",
                json={"identity": self._identity, "secret": self._secret},
                ssl=self._get_ssl_context(),
            )
        except Exception as err:
            _LOGGER.error(
                "NPMplus connection error (%s): %s", type(err).__name__, err
            )
            raise NPMplusConnectionError(
                f"Cannot connect to NPMplus at {self._base_url}: {err}"
            ) from err

        if resp.status in (400, 401, 403):
            data = await resp.json()
            raise NPMplusAuthError(
                f"Invalid credentials (status {resp.status}): {data}"
            )

        if resp.status != 200:
            raise NPMplusConnectionError(f"Unexpected status {resp.status}")

        data = await resp.json()
        token = data.get("token")
        if token:
            self._token = token
            _LOGGER.debug("Authenticated with Bearer token (NPM)")
        else:
            _LOGGER.debug("Authenticated with session cookie (NPMplus)")

        self._authenticated = True

    def _auth_headers(self) -> dict[str, str]:
        """Return Bearer auth header if using token auth."""
        if self._token:
            return {"Authorization": f"Bearer {self._token}"}
        return {}

    async def _request(
        self, method: str, path: str, **kwargs: Any
    ) -> aiohttp.ClientResponse:
        """Make an authenticated API request with auto re-auth on 401."""
        session = await self._ensure_session()

        if not self._authenticated:
            await self.async_authenticate()

        url = f"{self._base_url}{path}"

        try:
            resp = await session.request(
                method, url, ssl=self._get_ssl_context(),
                headers=self._auth_headers(), **kwargs
            )
        except (aiohttp.ClientError, TimeoutError) as err:
            raise NPMplusConnectionError(
                f"Cannot connect to NPMplus at {self._base_url}"
            ) from err

        if resp.status == 401:
            # Auth expired — re-authenticate once
            await self.async_authenticate()
            try:
                resp = await session.request(
                    method, url, ssl=self._get_ssl_context(),
                    headers=self._auth_headers(), **kwargs
                )
            except (aiohttp.ClientError, TimeoutError) as err:
                raise NPMplusConnectionError(
                    f"Cannot connect to NPMplus at {self._base_url}"
                ) from err

        if resp.status in (401, 403):
            raise NPMplusAuthError("Authentication failed")

        if resp.status >= 400:
            raise NPMplusConnectionError(
                f"NPMplus API error: {method} {path} returned status {resp.status}"
            )

        return resp

    async def async_get_proxy_hosts(self) -> list[dict[str, Any]]:
        """Fetch all proxy hosts."""
        resp = await self._request("GET", "/api/nginx/proxy-hosts")
        data = await resp.json(content_type=None)
        if not isinstance(data, list):
            raise NPMplusConnectionError(
                f"Unexpected API response for proxy hosts: expected list, got {type(data).__name__}"
            )
        return data

    async def async_enable_proxy_host(self, host_id: int) -> None:
        """Enable a proxy host."""
        await self._request("POST", f"/api/nginx/proxy-hosts/{host_id}/enable")

    async def async_disable_proxy_host(self, host_id: int) -> None:
        """Disable a proxy host."""
        await self._request("POST", f"/api/nginx/proxy-hosts/{host_id}/disable")
