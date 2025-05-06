"""FuelSnoop data source for Australia (QLD)."""

import logging
import json

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_SOURCE_ID,
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS
)
from pyfuelprices.fuel_locations import FuelLocation, Fuel
from pyfuelprices.helpers import geocoder
from pyfuelprices.sources import Source

from .const import PETROLSPY_API_HEADERS, PETROLSPY_API_SITES

_LOGGER = logging.getLogger(__name__)

class PetrolSpySource(Source):
    """PetrolSpy data source."""
    provider_name = "petrolspy"
    _fuel_products: list[str] = []
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None

    async def _send_request(self, url):
        """Send a HTTP request to the API and return the text."""
        async with self._client_session.get(
            url,
            headers=PETROLSPY_API_HEADERS) as response:
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
        if radius > 15.0:
            _LOGGER.warning("Radius %s too large for this provider. Limiting to %s", radius, 15.0)
            radius = 15.0
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
        _LOGGER.debug("Searching PetrolSpy for FuelLocations at area %s",
                        area)
        bbox = geocoder.get_bounding_box(
            area[PROP_AREA_LAT],
            area[PROP_AREA_LONG],
            area[PROP_AREA_RADIUS]
        )
        response_raw = await self._send_request(
            url=PETROLSPY_API_SITES.format(
                LAT_MAX=bbox.lat_max,
                LNG_MAX=bbox.lon_max,
                LAT_MIN=bbox.lat_min,
                LNG_MIN=bbox.lon_min
            )
        )
        if response_raw is not None:
            await self.parse_response(json.loads(response_raw))
            return True
        return False

    async def parse_response(self, response) -> list[FuelLocation]:
        for station in response["message"]["list"]:
            await self.parse_raw_fuel_station(station=station)
        return list(self.location_cache.values())

    async def parse_raw_fuel_station(self, station) -> FuelLocation:
        """Convert an instance of a single fuel station into a FuelLocation."""
        site_id = f"{self.provider_name}_{station['id']}"
        _LOGGER.debug("Parsing PetrolSpy location ID %s", site_id)
        loc = FuelLocation.create(
            site_id=site_id,
            name=station["name"],
            address=station['address'],
            lat=station['location']['y'],
            long=station['location']['x'],
            brand=station['brand'],
            available_fuels=self.parse_fuels(station.get("prices", [])),
            postal_code=station['postCode'],
            currency="AUD" if station["country"] == "AU" else "NZD",
            props={
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: station["id"],
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                "data": station
            }
        )
        loc.next_update = self.next_update + self.update_interval
        if site_id not in self.location_cache:
            self.location_cache[site_id] = loc
        else:
            await self.location_cache[site_id].update(loc)
        return self.location_cache[site_id]

    def parse_fuels(self, fuels: dict) -> list[Fuel]:
        output = []
        for k in fuels:
            f = fuels[k]
            output.append(Fuel(
                fuel_type=k,
                cost=f["amount"]/100,
                props=f
            ))
        return output
