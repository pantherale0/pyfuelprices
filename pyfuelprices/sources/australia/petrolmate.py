"""Petrolmate data source for Australia and New Zealand."""

import json
import logging

from pyfuelprices.const import (
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_SOURCE_ID,
)
from pyfuelprices.fuel_locations import Fuel, FuelLocation
from pyfuelprices.sources import Source

from .const import PETROLMATE_API_HEADERS, PETROLMATE_API_SITES

_LOGGER = logging.getLogger(__name__)

MILES_TO_METRES = 1609.344
PETROLMATE_MAX_RADIUS_M = 25000
PETROLMATE_MAX_LIMIT = 50


class PetrolmateSource(Source):
    """Petrolmate data source."""

    country_code = ["AU", "NZ"]

    provider_name = "petrolmate"
    _fuel_products: list[str] = []
    location_cache: dict[str, FuelLocation] = {}

    async def _send_request(self, url):
        """Send a HTTP request to the API and return the text."""
        async with self._client_session.get(url, headers=PETROLMATE_API_HEADERS) as response:
            if response.ok:
                return await response.text()
            _LOGGER.error("Error sending request to %s: %s", url, response)

    async def search_sites(self, coordinates, radius: float) -> list[dict]:
        """Return all available sites within a given radius."""
        # first query the API to populate cache / update data in case this data is unavailable.
        data = await super().search_sites(coordinates, radius)
        if len(data) > 0:
            return data
        await self.update(
            areas=[{PROP_AREA_LAT: coordinates[0], PROP_AREA_LONG: coordinates[1], PROP_AREA_RADIUS: radius}],
            force=True,
        )
        return await super().search_sites(coordinates, radius)

    async def update_area(self, area) -> bool:
        """Update a given area."""
        _LOGGER.debug("Searching Petrolmate for FuelLocations at area %s", area)
        radius_m = min(round(area[PROP_AREA_RADIUS] * MILES_TO_METRES), PETROLMATE_MAX_RADIUS_M)
        response_raw = await self._send_request(
            url=PETROLMATE_API_SITES.format(
                LAT=area[PROP_AREA_LAT], LNG=area[PROP_AREA_LONG], RADIUS=radius_m, LIMIT=PETROLMATE_MAX_LIMIT
            )
        )
        if response_raw is not None:
            await self.parse_response(json.loads(response_raw))
            return True
        return False

    async def parse_response(self, response) -> list[FuelLocation]:
        for station in response.get("stations", []):
            await self.parse_raw_fuel_station(station=station)
        return list(self.location_cache.values())

    async def parse_raw_fuel_station(self, station) -> FuelLocation:
        """Convert an instance of a single fuel station into a FuelLocation."""
        site_id = f"{self.provider_name}_{station['id']}"
        _LOGGER.debug("Parsing Petrolmate location ID %s", site_id)
        loc = FuelLocation.create(
            site_id=site_id,
            name=station["name"],
            address=station.get("address", ""),
            lat=station["lat"],
            long=station["lng"],
            brand=station.get("brand", "OTHER"),
            available_fuels=self.parse_fuels(station.get("fuels", [])),
            postal_code=station.get("postcode", ""),
            currency="AUD" if station.get("country") == "AU" else "NZD",
            props={
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: station["id"],
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                "data": station,
            },
        )
        loc.next_update = self.next_update + self.update_interval
        if site_id not in self.location_cache:
            self.location_cache[site_id] = loc
        else:
            await self.location_cache[site_id].update(loc)
        return self.location_cache[site_id]

    def parse_fuels(self, fuels: list) -> list[Fuel]:
        output = []
        for f in fuels:
            output.append(Fuel(fuel_type=f["type"], cost=f["price"] / 100, props=f))
        return output
