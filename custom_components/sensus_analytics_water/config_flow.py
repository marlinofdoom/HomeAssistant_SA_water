"""Config flow for Sensus Analytics Integration (Water)."""

from __future__ import annotations

import logging

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_ACCOUNT_NUMBER,
    CONF_BASE_URL,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_WATER_METER_NUMBER,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class SensusAnalyticsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sensus Analytics Integration."""

    VERSION = 1

    def is_matching(self, other_flow):
        """Determine if this flow matches another flow."""
        # Implement matching logic if necessary
        return False  # Return False if you don't have specific matching logic

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            _LOGGER.debug("User input: %s", user_input)
            # Set a unique ID based on account and meter number
            unique_id = f"{user_input[CONF_ACCOUNT_NUMBER]}_{user_input[CONF_WATER_METER_NUMBER]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # Validate the user input (e.g., test the connection)
            valid = await self._test_credentials(user_input)
            if valid:
                return self.async_create_entry(title="Sensus Analytics", data=user_input)
            errors["base"] = "auth"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL): str,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_ACCOUNT_NUMBER): str,
                vol.Required(CONF_WATER_METER_NUMBER): str,
                vol.Required("water_unit_type", default="gal"): vol.In(["CCF", "gal"]),
                vol.Optional("water_tier1_gallons"): cv.positive_float,
                vol.Required("water_tier1_price", default=0.0128): cv.positive_float,
                vol.Optional("water_tier2_gallons"): cv.positive_float,
                vol.Optional("water_tier2_price"): cv.positive_float,
                vol.Optional("water_tier3_price"): cv.positive_float,
                vol.Required("water_service_fee", default=15.00): cv.positive_float,
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def _test_credentials(self, user_input) -> bool:
        """Test if the provided credentials are valid."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{user_input[CONF_BASE_URL]}/j_spring_security_check",
                    data={
                        "j_username": user_input[CONF_USERNAME],
                        "j_password": user_input[CONF_PASSWORD],
                    },
                    allow_redirects=False,
                    timeout=10,
                ) as response:
                    _LOGGER.debug("Authentication response status: %s", response.status)
                    return response.status == 302
        except aiohttp.ClientError as error:
            _LOGGER.error("Error validating credentials: %s", error)
            return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return SensusAnalyticsOptionsFlow(config_entry)


class SensusAnalyticsOptionsFlow(config_entries.OptionsFlow):
    """Handle Sensus Analytics options."""

    def __init__(self, config_entry):
        """Initialize SensusAnalytics options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            _LOGGER.debug("User updated options: %s", user_input)
            # Update the entry with new options
            self.hass.config_entries.async_update_entry(self.config_entry, data=user_input)
            # Force a sensor refresh
            coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]
            await coordinator.async_request_refresh()
            return self.async_create_entry(title="", data={})

        # Fetch current configuration data
        current_data = self.config_entry.data

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_BASE_URL,
                    default=current_data.get(CONF_BASE_URL),
                ): str,
                vol.Required(
                    CONF_USERNAME,
                    default=current_data.get(CONF_USERNAME),
                ): str,
                vol.Required(
                    CONF_PASSWORD,
                    default=current_data.get(CONF_PASSWORD),
                ): str,
                vol.Required(
                    CONF_ACCOUNT_NUMBER,
                    default=current_data.get(CONF_ACCOUNT_NUMBER),
                ): str,
                vol.Required(
                    CONF_WATER_METER_NUMBER,
                    default=current_data.get(CONF_WATER_METER_NUMBER),
                ): str,
                vol.Required(
                    "water_unit_type",
                    default=current_data.get("water_unit_type", "gal"),
                ): vol.In(["CCF", "gal"]),
                vol.Optional(
                    "water_tier1_gallons",
                    default=current_data.get("water_tier1_gallons"),
                ): cv.positive_float,
                vol.Required(
                    "water_tier1_price",
                    default=current_data.get("water_tier1_price", 0.0128),
                ): cv.positive_float,
                vol.Optional(
                    "water_tier2_gallons",
                    default=current_data.get("water_tier2_gallons"),
                ): cv.positive_float,
                vol.Optional(
                    "water_tier2_price",
                    default=current_data.get("water_tier2_price"),
                ): cv.positive_float,
                vol.Optional(
                    "water_tier3_price",
                    default=current_data.get("water_tier3_price"),
                ): cv.positive_float,
                vol.Required(
                    "water_service_fee",
                    default=current_data.get("water_service_fee", 15.00),
                ): cv.positive_float,
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
