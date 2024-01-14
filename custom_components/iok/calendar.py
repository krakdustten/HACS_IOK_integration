import datetime
import logging
from typing import Optional, List

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .iok_base import IokBase
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant

from .const import CITY, DOMAIN, STREET


_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, async_add_entities, discovery_info=None):
    if discovery_info and "config" in discovery_info:
        conf = discovery_info["config"]
    else:
        conf = config

    if not conf:
        return

    async_add_entities([IOKCalendar(hass.data[DOMAIN][conf.entry_id], conf)])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([IOKCalendar(hass.data[DOMAIN][entry.entry_id], entry)])


class IOKCalendar(CoordinatorEntity, CalendarEntity):
    _attr_icon = "mdi:delete-empty"

    def __init__(self, coordinator, config) -> None:
        super().__init__(coordinator, context=config.entry_id)
        self.config = config
        self.coordinator = coordinator

        self._attr_name = "IOK"

    @property
    def event(self) -> Optional[CalendarEvent]:
        """Return the next upcoming event."""
        today = datetime.date.today()
        events = self.get_all_events(today, today + timedelta(days=14))
        return events[0]

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        return self.get_all_events(start_date.date(), end_date.date())

    def get_all_events(self, start_date: datetime.date, end_date: datetime.date):
        events: List[CalendarEvent] = []
        base = self.coordinator.iok_base
        for event in base.data:
            date, waste = event
            if start_date > date > end_date:
                continue
            events.append(
                CalendarEvent(
                    summary=", ".join(waste), start=date, end=date + timedelta(days=1)
                )
            )
        return events

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
