"""The iok_integration integration."""
from __future__ import annotations
from datetime import timedelta

import logging
import async_timeout
from .calendar import IOKCalendar

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import CITY, DOMAIN, STREET
from .iok_base import IokBase

_LOGGER = logging.getLogger(__name__)

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up iok_integration from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    iok_base = IokBase(entry.data[CITY], entry.data[STREET])
    coordinator = IokCoordinator(hass, iok_base)
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class IokCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, iok_base: IokBase):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="IokInterface",
            update_interval=timedelta(hours=12),
        )
        self.iok_base = iok_base

    async def _async_update_data(self):
        """
        Fetch data from API endpoint.
        """
        try:
            await self.iok_base.update_data_from_api()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
