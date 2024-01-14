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
        for day in base.this_month_data:
            date = datetime.datetime(base.this_year, base.this_month, day)
            if start_date > date.date() > end_date:
                continue
            if len(base.this_month_data[day]) > 0:
                events.append(
                    CalendarEvent(
                        summary=", ".join(base.this_month_data[day]),
                        start=date.date(),
                        end=date.date() + timedelta(days=1),
                    )
                )
        for day in base.next_month_data:
            date = datetime.datetime(base.next_month_year, base.next_month, day)
            if start_date > date.date() > end_date:
                continue
            if len(base.next_month_data[day]) > 0:
                events.append(
                    CalendarEvent(
                        summary=", ".join(base.next_month_data[day]),
                        start=date.date(),
                        end=date.date() + timedelta(days=1),
                    )
                )
        return events

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
