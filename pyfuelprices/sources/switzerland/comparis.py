"""Comparis data source."""

import logging
import json
import re

from datetime import datetime

from pyfuelprices.const import (
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID,
    DESKTOP_USER_AGENT
)
from pyfuelprices.fuel_locations import Fuel, FuelLocation
from pyfuelprices.sources import (
    Source,
    geocode_reverse_lookup,
    geopyexc
)

_LOGGER = logging.getLogger(__name__)

CONST_COMPARIS_PAGE = "https://www.comparis.ch/benzin-preise"
CONST_COMPARIS_DATA_ID = "__NEXT_DATA__"

class ComparisSource(Source):
    """Comparis Source."""
    _headers = {
        "User-Agent": DESKTOP_USER_AGENT,
        "Content-Length":"0"
    }
    provider_name = "comparis"
    location_cache: dict[str, FuelLocation] = {}
    # location_tree = None

    async def _send_request(self, postcode, radius):
        """Send a request to the API for a given postcode and radius."""
        radius = radius * 1.609344 # convert miles to km
        url = CONST_COMPARIS_PAGE
        _LOGGER.debug("Sending request to Comparis: %s",
                      url)
        async with self._client_session.get(
            url,
            headers=self._headers) as response:
            if response.status == 200:
                await response.text()
                _LOGGER.debug(response.content)
                pattern = r'<script id="' + CONST_COMPARIS_DATA_ID + r'".*?>(.*?)</script>'
                html_content = await response.text()
                script_content = re.search(pattern, html_content, re.DOTALL)
                if script_content:
                    extracted_content = script_content.group(1).strip()
                    _LOGGER.debug("Content within script tag with id='__NEXT_DATA__':")
                    return extracted_content
                else:
                    _LOGGER.error("Script tag with id='__NEXT_DATA__' not found in the HTML content.")
            _LOGGER.error("Error sending request to %s: %s",
                            url,
                            response)
            return "{}"

    async def update(self, areas=None, force=None) -> list[FuelLocation]:
        """Custom update handler as this needs to query Comparis on areas."""
        if datetime.now() > self.next_update:
            self._configured_areas=[] if areas is None else areas
            for area in self._configured_areas:
                try:
                    geocode = await geocode_reverse_lookup(
                        (area[PROP_AREA_LAT], area[PROP_AREA_LONG])
                    )
                except geopyexc.GeocoderTimedOut:
                    _LOGGER.warning("Timeout occured while geocoding area %s.",
                                    area)
                    continue
                if geocode.raw["address"]["country_code"] != "ch":
                    _LOGGER.debug("Skipping area %s as not in CH.",
                                area)
                    continue
                response_raw = json.loads(await self._send_request(
                    postcode=geocode.raw["address"]["postcode"],
                    radius=area[PROP_AREA_RADIUS]
                ))
                
                if len(response_raw) != 0:
                    response_raw = response_raw["props"]["pageProps"]
                    await self.parse_response(response_raw["data"])
                else:
                    _LOGGER.error("Error sending request to %s: %s",
                                self.provider_name,
                                response_raw)
            self.next_update += self.update_interval
        return list(self.location_cache.values())

    def _parse_raw(self, station: dict) -> FuelLocation:
        """Parse a single raw instance of a fuel site."""
        site_id = f"{self.provider_name}_{station['id']}"
        _LOGGER.debug("Parsing Comparis location ID %s", site_id)
        plz_pattern = r'\d{4}'
        match = re.search(plz_pattern, station["formattedAddress"])
        if match:
            postal_code = match.group()
        else:
            postal_code = None
        loc = FuelLocation.create(
            site_id=site_id,
            name=station["displayName"],
            address=station["formattedAddress"],
            lat=station["location"]["lat"],
            long=station["location"]["lng"],
            brand=station["brand"],
            available_fuels=self.parse_fuels(station["fuelCollection"]),
            postal_code=postal_code,
            currency="CHF",
            props={
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: station["id"],
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                "opening_times": station.get("openingTimes", {}).get("openingTimes", [])
            }
        )
        loc.next_update = self.next_update if self.next_update > datetime.now() else (
            self.next_update + self.update_interval
        )
        return loc

    async def parse_response(self, response) -> list[FuelLocation]:
        for station_raw in response:
            station = self._parse_raw(station_raw)
            if station.id not in self.location_cache:
                self.location_cache[station.id] = station
            else:
                await self.location_cache[station.id].update(station)
        return list(self.location_cache.values())

    def parse_fuels(self, fuels: dict[str, object]) -> list[Fuel]:
        """Parse fuel data from Comparis."""
        fuels_parsed = []
        for k in fuels:
            if fuels[k] != None:
                fuels_parsed.append(Fuel(
                    fuel_type=str(k).upper(),
                    cost=fuels[k]["displayPrice"],
                    props={}
                ))
        return fuels_parsed
