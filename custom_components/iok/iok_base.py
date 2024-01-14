import logging

from typing import List, Dict, Optional
import datetime
import aiohttp
from bs4 import BeautifulSoup


_LOGGER = logging.getLogger(__name__)


class IokBase:
    def __init__(self, city: str, street: str) -> None:
        """Initialize."""
        self.city = city
        self.street = street

        self.data = []

    async def test_connection(self) -> bool:
        _LOGGER.info(
            "Testing connection with city '%s' and street '%s'", self.city, self.street
        )
        today = datetime.date.today()
        year = today.year
        try:
            ses = await _open_sesion(self.city, self.street)
            await _get_month(ses, year, 1)
            await ses.close()
        except Exception as e:
            _LOGGER.info("ERROR %s", str(e))
            return False
        return True

    async def update_data_from_api(self):
        today = datetime.date.today()
        year = today.year
        month = today.month
        try:
            ses = await _open_sesion(self.city, self.street)
            data = []
            for i in range(12):
                m = month + i
                y = year
                if m > 12:
                    y = year + 1
                    m = m - 12
                days = await _get_month(ses, y, m)
                for day in days:
                    d = days[day]
                    if len(d) > 0:
                        data.append((
                            datetime.datetime(y, m, day).date(),
                            d
                        ))

            self.data = data

            await ses.close()
        except Exception as e:
            _LOGGER.info("ERROR %s", str(e))


async def _open_sesion(
    city: str, street: str, ses: Optional[aiohttp.ClientSession] = None
) -> aiohttp.ClientSession:
    if ses is None:
        ses = aiohttp.ClientSession(raise_for_status=False)

    base_site = await ses.get("https://www.iok.be/afvalkalender")
    base_site_dom = BeautifulSoup(await base_site.text(), features="html.parser")
    base_site_from_id = base_site_dom.find("input", {"name": "form_build_id"})
    form_build_id = base_site_from_id.attrs["value"]

    post_city_site = await ses.post(
        "https://www.iok.be/adres-kiezen?return=/afvalkalender&ajax_form=1&_wrapper_format=drupal_ajax",
        data={
            "city": city,
            "form_build_id": form_build_id,
            "form_id": "e2e_iok_address_form",
            "_triggering_element_name": "city",
            "_drupal_ajax": "1",
        },
    )
    post_city_json = await post_city_site.json()
    for command in post_city_json:
        if command["command"] == "update_build_id":
            form_build_id = command["new"]

    post_street_site = await ses.post(
        "https://www.iok.be/adres-kiezen?_wrapper_format=drupal_ajax&ajax_form=1&return=/afvalkalender&_wrapper_format=drupal_ajax",
        data={
            "city": city,
            "form_build_id": form_build_id,
            "form_id": "e2e_iok_address_form",
            "street": street,
            "_triggering_element_name": "street",
            "_drupal_ajax": "1",
        },
    )
    post_street_json = await post_street_site.json()
    for command in post_street_json:
        if command["command"] == "update_build_id":
            form_build_id = command["new"]

    post_site = await ses.post(
        "https://www.iok.be/adres-kiezen?return=/afvalkalender",
        data={
            "city": city,
            "form_build_id": form_build_id,
            "form_id": "e2e_iok_address_form",
            "street": street,
            "op": "Opslaan",
        },
    )

    return ses


async def _get_month(
    ses: aiohttp.ClientSession, year: int, month: int
) -> Dict[int, List[str]]:
    retd = {}
    base_site = await ses.get(
        "https://www.iok.be/afvalkalender", params={"year": year, "month": month}
    )
    base_site_dom = BeautifulSoup(await base_site.text(), features="html.parser")

    ioktable = base_site_dom.find("div", {"class": "iokcalendar"}).div.table
    for row in ioktable.contents:
        if not row.name == "tr":
            continue
        for col in row.contents:
            if not col.name == "td":
                continue
            if (
                "weekday" not in col.attrs["class"]
                and "weekend" not in col.attrs["class"]
            ):
                continue
            day = int(col.contents[0].text)
            waste = []
            for wd in col.contents[1:]:
                waste.append(wd.a.text)
            retd[day] = waste
    return retd
