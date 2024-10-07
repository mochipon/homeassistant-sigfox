"""Config flow for the Sigfox integration."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .api import SigfoxAPI, AuthenticationError
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)


class SigfoxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sigfox."""

    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            api = SigfoxAPI(username, password)

            try:
                # Authenticate by fetching devices
                devices = await api.get_all_devices()
                if devices:
                    _LOGGER.debug(
                        f"Authentication successful, devices found: {devices}"
                    )
                    # Proceed to create the config entry
                    return self.async_create_entry(
                        title="Sigfox Devices",
                        data={
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                        },
                    )
                else:
                    _LOGGER.error("Authentication successful but no devices found")
                    errors["base"] = "no_devices_found"
            except AuthenticationError:
                _LOGGER.warning(f"Authentication failed for user: {username}")
                errors["base"] = "auth"
            except Exception as e:
                _LOGGER.exception("Unexpected exception: %s", e)
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return SigfoxOptionsFlow(config_entry)


class SigfoxOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Sigfox."""

    def __init__(self, config_entry):
        """Initialize Sigfox options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the Sigfox options."""
        return self.async_show_form(step_id="init")
