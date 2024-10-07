# coordinator.py

"""DataUpdateCoordinator for the Sigfox integration."""

from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant

from .api import SigfoxAPI, RateLimitError

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)


class SigfoxDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Sigfox data."""

    def __init__(self, hass: HomeAssistant, api: SigfoxAPI) -> None:
        """Initialize the coordinator."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name="Sigfox Data Coordinator",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from Sigfox API."""
        try:
            devices = await self.api.get_all_devices()
            device_data = {device["id"]: device for device in devices}
            _LOGGER.debug(f"Data fetched by coordinator: {device_data}")
            return device_data
        except RateLimitError:
            _LOGGER.error("Rate limit exceeded when fetching devices")
            return {}
