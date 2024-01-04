"""TankerKoenig data source."""

import logging
import json

import aiohttp

from pyfuelprices.const import (
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID
)
from pyfuelprices.fuel_locations import Fuel, FuelLocation
from pyfuelprices.sources import (
    Source,
    geocode_reverse_lookup
)

_LOGGER = logging.getLogger(__name__)

CONST_TANKERKOENIG_API_BASE = "https://tankerkoenig.de/ajax_v3_public/"
CONST_TANKERKOENIG_GET_STATIONS = (
    f"{CONST_TANKERKOENIG_API_BASE}get_stations_near_postcode.php"
    "?postcode={POSTCODE}&radius={RADIUS}"
)

class TankerKoenigSource(Source):
    """TankerKoenig Source."""
    _headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
    }
    provider_name = "tankerkoenig"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None

    async def _send_request(self, postcode, radius):
        """Send a request to the API for a given postcode and radius."""
        radius = radius * 1.609344 # convert miles to km
        url = CONST_TANKERKOENIG_GET_STATIONS.format(
            POSTCODE=postcode,
            RADIUS=radius
        )
        _LOGGER.debug("Sending request to TankerKoenig: %s",
                      url)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.ok:
                    return await response.text()
                _LOGGER.error("Error sending request to %s: %s",
                              url,
                              response)

    async def update(self, areas=None) -> list[FuelLocation]:
        """Custom update handler as this needs to query TankerKoenig on areas."""
        self._configured_areas=[] if areas is None else areas
        for area in self._configured_areas:
            geocode = await geocode_reverse_lookup(
                (area[PROP_AREA_LAT], area[PROP_AREA_LONG])
            )
            if geocode.raw["address"]["country_code"] != "de":
                _LOGGER.debug("Skipping area %s as not in DE.",
                              area)
                continue
            response_raw = json.loads(await self._send_request(
                postcode=geocode.raw["address"]["postcode"],
                radius=area[PROP_AREA_RADIUS]
            ))
            if response_raw["ok"]:
                await self.parse_response(response_raw["data"])
            else:
                _LOGGER.error("Error sending request to %s: %s",
                              self.provider_name,
                              response_raw)
        return list(self.location_cache.values())

    def _parse_raw(self, station: dict) -> FuelLocation:
        """Parse a single raw instance of a fuel site."""
        site_id = f"{self.provider_name}_{station['id']}"
        _LOGGER.debug("Parsing TankerKoenig location ID %s", site_id)
        return FuelLocation.create(
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
