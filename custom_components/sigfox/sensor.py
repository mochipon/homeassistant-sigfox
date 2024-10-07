"""Sensor platform for the Sigfox integration."""

from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD
from .api import SigfoxAPI, RateLimitError
from .coordinator import SigfoxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=15)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up Sigfox sensors from a config entry."""
    config = config_entry.data
    username = config.get(CONF_USERNAME, "")
    password = config.get(CONF_PASSWORD, "")

    api = SigfoxAPI(username, password)

    coordinator = SigfoxDataUpdateCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    entities = []

    for device_id, device_info in coordinator.data.items():
        device_name = device_info.get("name", device_id)

        entities.extend(
            [
                SigfoxDeviceStatusSensor(coordinator, device_id, device_name),
                SigfoxComStateSensor(coordinator, device_id, device_name),
                SigfoxLastComSensor(coordinator, device_id, device_name),
                SigfoxLqiSensor(coordinator, device_id, device_name),
                SigfoxActivationTimeSensor(coordinator, device_id, device_name),
                SigfoxCreationTimeSensor(coordinator, device_id, device_name),
                SigfoxAutomaticRenewalSensor(coordinator, device_id, device_name),
                SigfoxLastMessageSensor(api, device_id, device_name),
            ]
        )

    async_add_entities(entities)


def convert_epoch_to_datetime(epoch_ms: Optional[int]) -> Optional[datetime]:
    """Convert milliseconds since Unix Epoch to a UTC datetime object."""
    if epoch_ms is None:
        return None
    # Create a UTC datetime object
    dt = datetime.utcfromtimestamp(epoch_ms / 1000)
    dt = dt.replace(tzinfo=dt_util.UTC)
    return dt


class SigfoxSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for all Sigfox sensors."""

    def __init__(
        self, coordinator: SigfoxDataUpdateCoordinator, device_id: str, device_name: str
    ) -> None:
        """Initialize the Sigfox sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.device_name = device_name

        self._attr_device_info = {
            "identifiers": {(DOMAIN, self.device_id)},
            "name": self.device_name,
            "manufacturer": "Sigfox",
            "model": "Sigfox Device",
        }
        self._attr_unique_id = f"{self.device_id}_{self.__class__.__name__}"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.device_id in self.coordinator.data
        )

    @property
    def device_info_data(self) -> Optional[Dict[str, Any]]:
        """Return the device info data from the coordinator."""
        return self.coordinator.data.get(self.device_id, None)


class SigfoxDeviceStatusSensor(SigfoxSensorBase):
    """Representation of a Sigfox device status sensor."""

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        """Initialize the device status sensor."""
        super().__init__(coordinator, device_id, device_name)
        self._attr_device_class = SensorDeviceClass.ENUM
        self.state_mapping: Dict[int, str] = {
            0: "OK",
            1: "DEAD",
            2: "OFF_CONTRACT",
            3: "DISABLED",
            5: "DELETED",
            6: "SUSPENDED",
            7: "NOT_ACTIVABLE",
        }
        self._attr_options = list(self.state_mapping.values())
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self.device_name} Status"

    @property
    def native_value(self) -> Optional[str]:
        """Return the native value of the sensor."""
        device_info = self.device_info_data
        if device_info:
            state_value = device_info.get("state")
            return self.state_mapping.get(state_value)
        return None


class SigfoxComStateSensor(SigfoxSensorBase):
    """Representation of the communication state of the Sigfox device."""

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        """Initialize the communication state sensor."""
        super().__init__(coordinator, device_id, device_name)
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self.com_state_mapping: Dict[int, str] = {
            0: "NO",
            1: "OK",
            3: "RED",
            4: "N/A",
            5: "NOT_SEEN",
        }
        self._attr_options = list(self.com_state_mapping.values())

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self.device_name} Communication State"

    @property
    def native_value(self) -> Optional[str]:
        """Return the native value of the sensor."""
        device_info = self.device_info_data
        if device_info:
            com_state_value = device_info.get("comState")
            return self.com_state_mapping.get(com_state_value)
        return None


class SigfoxLastComSensor(SigfoxSensorBase):
    """Representation of the last communication time of the Sigfox device."""

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        """Initialize the last communication sensor."""
        super().__init__(coordinator, device_id, device_name)
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self.device_name} Last Communication"

    @property
    def native_value(self) -> Optional[datetime]:
        """Return the native value of the sensor."""
        device_info = self.device_info_data
        if device_info:
            last_com_ms: Optional[int] = device_info.get("lastCom")
            return convert_epoch_to_datetime(last_com_ms)
        return None


class SigfoxLqiSensor(SigfoxSensorBase):
    """Representation of the Link Quality Indicator (LQI) of the Sigfox device."""

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        """Initialize the LQI sensor."""
        super().__init__(coordinator, device_id, device_name)
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self.lqi_mapping: Dict[int, str] = {
            0: "LIMIT",
            1: "AVERAGE",
            2: "GOOD",
            3: "EXCELLENT",
            4: "N/A",
        }
        self._attr_options = list(self.lqi_mapping.values())

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self.device_name} LQI"

    @property
    def native_value(self) -> Optional[str]:
        """Return the native value of the sensor."""
        device_info = self.device_info_data
        if device_info:
            lqi_value = device_info.get("lqi")
            return self.lqi_mapping.get(lqi_value)
        return None


class SigfoxActivationTimeSensor(SigfoxSensorBase):
    """Representation of the device's activation time."""

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        """Initialize the activation time sensor."""
        super().__init__(coordinator, device_id, device_name)
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self.device_name} Activation Time"

    @property
    def native_value(self) -> Optional[datetime]:
        """Return the native value of the sensor."""
        device_info = self.device_info_data
        if device_info:
            activation_time_ms = device_info.get("activationTime")
            return convert_epoch_to_datetime(activation_time_ms)
        return None


class SigfoxCreationTimeSensor(SigfoxSensorBase):
    """Representation of the device's creation time."""

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        """Initialize the creation time sensor."""
        super().__init__(coordinator, device_id, device_name)
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self.device_name} Creation Time"

    @property
    def native_value(self) -> Optional[datetime]:
        """Return the native value of the sensor."""
        device_info = self.device_info_data
        if device_info:
            creation_time_ms = device_info.get("creationTime")
            return convert_epoch_to_datetime(creation_time_ms)
        return None


class SigfoxAutomaticRenewalSensor(SigfoxSensorBase):
    """Representation of the device's automatic renewal status."""

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        """Initialize the automatic renewal sensor."""
        super().__init__(coordinator, device_id, device_name)
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self.state_mapping: Dict[bool, str] = {
            True: "Enabled",
            False: "Disabled",
        }
        self._attr_options = list(self.state_mapping.values())

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self.device_name} Automatic Renewal"

    @property
    def native_value(self) -> Optional[str]:
        """Return the native value of the sensor."""
        device_info = self.device_info_data
        if device_info:
            automatic_renewal = device_info.get("automaticRenewal")
            return self.state_mapping.get(automatic_renewal)
        return None


class SigfoxLastMessageSensor(SensorEntity):
    """Representation of the last message received by the Sigfox device."""

    def __init__(self, api: SigfoxAPI, device_id: str, device_name: str) -> None:
        """Initialize the last message sensor."""
        self.api = api
        self.device_id = device_id
        self.device_name = device_name

        self._attr_device_info = {
            "identifiers": {(DOMAIN, self.device_id)},
            "name": self.device_name,
            "manufacturer": "Sigfox",
            "model": "Sigfox Device",
        }
        self._attr_unique_id = f"{self.device_id}_LastMessageSensor"
        self._attr_extra_state_attributes: Dict[str, Any] = {}
        self._attr_native_value = None  # Initialize native_value
        self._attr_should_poll = True  # Enable polling

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self.device_name} Last Message"

    async def async_update(self) -> None:
        """Update the sensor state."""
        _LOGGER.debug(f"Updating SigfoxLastMessageSensor for device: {self.device_id}")
        try:
            messages = await self.api.get_device_messages(self.device_id)
            if messages and "data" in messages and len(messages["data"]) > 0:
                last_message = messages["data"][0]
                self._attr_native_value = last_message.get("data")
                self._attr_extra_state_attributes = {
                    "seq_number": last_message.get("seqNumber"),
                    "time": convert_epoch_to_datetime(last_message.get("time")),
                }
                _LOGGER.debug(
                    f"Last message for device {self.device_id}: {self._attr_native_value}"
                )
            else:
                self._attr_native_value = None
                self._attr_extra_state_attributes = {}
                _LOGGER.debug(f"No messages found for device {self.device_id}")
        except RateLimitError:
            _LOGGER.error(
                f"Rate limit exceeded when fetching messages for {self.device_id}"
            )
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
