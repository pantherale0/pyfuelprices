"""TankerKoenig data source."""

import logging
import json

from datetime import datetime, timedelta

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
from pyfuelprices.helpers import geopyexc, geocoder
from pyfuelprices.sources import (
    Source
)
from .const import (
    CONST_TANKERKOENIG_GET_STATIONS
)
_LOGGER = logging.getLogger(__name__)


class TankerKoenigSource(Source):
    """TankerKoenig Source."""
    _headers = {
        "User-Agent": DESKTOP_USER_AGENT
    }
    provider_name = "tankerkoenig"
    location_cache: dict[str, FuelLocation] = {}
    update_interval = timedelta(days=1)
    # location_tree = None

    async def _send_request(self, postcode, radius):
        """Send a request to the API for a given postcode and radius."""
        radius = radius * 1.609344 # convert miles to km
        url = CONST_TANKERKOENIG_GET_STATIONS.format(
            POSTCODE=postcode,
            RADIUS=radius
        )
        _LOGGER.debug("Sending request to TankerKoenig: %s",
                      url)
        async with self._client_session.get(
            url,
            headers=self._headers) as response:
            if response.ok:
                return await response.text()
            _LOGGER.error("Error sending request to %s: %s",
                            url,
                            response)

    async def search_sites(self, coordinates, radius: float) -> list[dict]:
        """Return all available sites within a given radius."""
        # first query the API to populate cache / update data in case this data is unavailable.
        data = await super().search_sites(coordinates, radius)
        if len(data)>0:
            return data
        await self.update(
            areas=[{
                PROP_AREA_LAT: coordinates[0],
                PROP_AREA_LONG: coordinates[1],
                PROP_AREA_RADIUS: radius
            }],
            force=True
        )
        return await super().search_sites(coordinates, radius)

    async def update_area(self, area) -> bool:
        """Update a given area."""
        try:
            geocode = await geocoder.geocode_reverse_lookup(
                (area[PROP_AREA_LAT], area[PROP_AREA_LONG])
            )
        except geopyexc.GeocoderTimedOut:
            _LOGGER.warning("Timeout occured while geocoding area %s.",
                            area)
            return False
        if geocode.raw["address"]["country_code"] != "de":
            _LOGGER.debug("Skipping area %s as not in DE.",
                        area)
            return False
        response_raw = json.loads(await self._send_request(
            postcode=geocode.raw["address"]["postcode"],
            radius=area[PROP_AREA_RADIUS]
        ))
        if response_raw["ok"]:
            await self.parse_response(response_raw["data"])
            return True
        _LOGGER.error("Error sending request to %s: %s",
                    self.provider_name,
                    response_raw)
        return False

    def _parse_raw(self, station: dict) -> FuelLocation:
        """Parse a single raw instance of a fuel site."""
        site_id = f"{self.provider_name}_{station['id']}"
        _LOGGER.debug("Parsing TankerKoenig location ID %s", site_id)
        loc = FuelLocation.create(
            site_id=site_id,
            name=station["name"],
            address=f"{station['house_number']} {station['street']} {station['post_code']}",
            lat=station["lat"],
            long=station["lng"],
            brand=station["brand"],
            available_fuels=self.parse_fuels(station["prices"]),
            postal_code=station['post_code'],
            currency="EUR",
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
        for station_raw in response.get("stations", []):
            station = self._parse_raw(station_raw)
            if station.id not in self.location_cache:
                self.location_cache[station.id] = station
            else:
                await self.location_cache[station.id].update(station)
        return list(self.location_cache.values())

    def parse_fuels(self, fuels: dict[str, object]) -> list[Fuel]:
        """Parse fuel data from TankerKoenig."""
        fuels_parsed = []
        for k in fuels:
            if k.find("_") < 0:
                fuels_parsed.append(Fuel(
                    fuel_type=str(k).upper(),
                    cost=fuels[k],
                    props={}
                ))
        return fuels_parsed
