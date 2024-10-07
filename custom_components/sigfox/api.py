"""Asynchronous client for the Sigfox API."""

import aiohttp
import asyncio
import async_timeout
from typing import List, Dict, Any
import logging

_LOGGER = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Exception raised when authentication fails."""


class RateLimitError(Exception):
    """Exception raised when the rate limit is exceeded."""


class SigfoxAPI:
    """Class to interact with the Sigfox API."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize the Sigfox API client."""
        self.base_url = "https://api.sigfox.com/v2"
        self.auth = aiohttp.BasicAuth(username, password)

    async def _make_request(self, url: str) -> Dict[str, Any]:
        """Internal function to send a request to the Sigfox API."""
        async with aiohttp.ClientSession(auth=self.auth) as session:
            try:
                async with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            _LOGGER.debug(f"API response for {url}: {data}")
                            return data
                        elif response.status == 401:
                            raise AuthenticationError("Invalid username or password")
                        elif response.status == 429:
                            _LOGGER.error(f"Rate limit exceeded for URL {url}")
                            raise RateLimitError("Rate limit exceeded")
                        else:
                            _LOGGER.error(
                                f"API request failed with status {response.status} for URL {url}"
                            )
                            return {}
            except asyncio.TimeoutError:
                _LOGGER.error(f"API request timed out for URL {url}")
                return {}
            except aiohttp.ClientError as e:
                _LOGGER.error(f"HTTP request failed: {e}")
                return {}

    async def get_all_devices(self) -> List[Dict[str, Any]]:
        """Retrieve all devices associated with the account."""
        url = f"{self.base_url}/devices"
        devices_data = await self._make_request(url)
        devices = devices_data.get("data", [])
        _LOGGER.debug(f"Devices fetched: {devices}")
        return devices

    async def get_device_messages(
        self, device_id: str, limit: int = 1
    ) -> Dict[str, Any]:
        """Retrieve messages from a device."""
        url = f"{self.base_url}/devices/{device_id}/messages?limit={limit}"
        messages = await self._make_request(url)
        _LOGGER.debug(f"Messages fetched for device {device_id}: {messages}")
        return messages
