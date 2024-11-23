"""Austria spritpreisrechner data source."""

from datetime import datetime

import asyncio
import logging
import json

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_SOURCE_ID,
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS,
    DESKTOP_USER_AGENT,
)
from pyfuelprices.fuel_locations import FuelLocation, Fuel
from pyfuelprices.sources import Source
from pyfuelprices.helpers import geocode_reverse_lookup

_LOGGER = logging.getLogger(__name__)

CONST_API_BASE = "https://www.spritpreisrechner.at/api"
CONST_API_SEARCH_REGIONS = (
    f"{CONST_API_BASE}/search/gas-stations/by-region?"
    "code={REG_CODE}&fuelType={FUEL_TYPE}&includeClosed=true&type={REG_TYPE}"
)
CONST_API_SEARCH_ADDRESS = (
    f"{CONST_API_BASE}/search/gas-stations/by-address?"
    "latitude={LAT}&longitude={LONG}&fuelType={FUEL_TYPE}&includeClosed=true"
)
CONST_API_GET_REGIONS = f"{CONST_API_BASE}/regions"
CONST_FUELS = ["DIE", "SUP", "GAS"]


class SpripreisrechnerATSource(Source):
    """Data source for spritpreisrechner."""

    provider_name = "spritpreisrechner"
    _headers = {"User-Agent": DESKTOP_USER_AGENT}
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
    _regions = []

    async def _send_request(self, url):
        """Send a HTTP request to the API."""
        async with self._client_session.get(url, headers=self._headers) as response:
            if response.ok:
                return await response.text()
            _LOGGER.error("Error sending request to %s: %s", url, response)

    async def _load_regions(self):
        """Load regions into memory."""
        self._regions = json.loads(await self._send_request(CONST_API_GET_REGIONS))

    def _parse_raw_fuel_station(self, station, site_id) -> FuelLocation:
        """Parse a raw fuel station."""
        _LOGGER.debug("Parsing %s location ID %s", self.provider_name, site_id)
        loc = FuelLocation.create(
            site_id=site_id,
            name=station.get("name", f"Unknown {station['id']}"),
            address=station["location"]["address"],
            lat=station["location"]["latitude"],
            long=station["location"]["longitude"],
            brand="unavailable",
            available_fuels=[
                Fuel(
                    fuel_type=f["label"],
                    cost=f["amount"],
                    props=f
                ) for f in station["prices"]
            ],
            postal_code=station["location"]["postalCode"],
            currency="EUR",
            props={
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: station["id"],
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                "data": station,
            },
        )
        loc.next_update = self.next_update + self.update_interval
        return loc

    def _update_fuel_station_prices(self, station, site_id):
        """Internal method to update station prices."""
        if len(station["prices"]) > 0:
            fuel = station["prices"][0]
            try:
                self.location_cache[site_id].get_fuel(fuel["label"]).update(
                    fuel_type=fuel["label"], cost=fuel["amount"], props=fuel
                )
            except ValueError:
                self.location_cache[site_id].available_fuels.append(
                    Fuel(fuel_type=fuel["label"], cost=fuel["amount"], props=fuel)
                )
            self.location_cache[site_id].last_updated = datetime.now()
            self.location_cache[site_id].next_update = self.next_update + self.update_interval

    async def update_area(self, area: dict):
        """Update given areas."""
        _LOGGER.debug("Searching FuelGR for FuelLocations at area %s", area)
        parser_coords = (area[PROP_AREA_LAT], area[PROP_AREA_LONG])
        geocoded = await geocode_reverse_lookup(parser_coords)
        if geocoded is None:
            _LOGGER.debug("Geocode failed, skipping area %s", area)
            return
        if geocoded.raw["address"]["country_code"] not in ["at"]:
            _LOGGER.debug("Geocode not within AT, skipping area %s", area)
            return
        for fuel in CONST_FUELS:
            await self.parse_response(
                json.loads(
                    await self._send_request(
                        url=CONST_API_SEARCH_ADDRESS.format(
                            LAT=area[PROP_AREA_LAT], LONG=area[PROP_AREA_LONG], FUEL_TYPE=fuel
                        )
                    )
                )
            )

    async def update_region(self, region_code, region_type):
        """Update fuels for a given region."""
        for fuel in CONST_FUELS:
            url = CONST_API_SEARCH_REGIONS.format(
                REG_CODE=region_code, FUEL_TYPE=fuel, REG_TYPE=region_type
            )
            await self.parse_response(json.loads(await self._send_request(url)))

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

    async def update(self, areas=None, force: bool | None = None) -> list[FuelLocation]:
        """Custom update handler to query each region."""
        if (datetime.now() > self.next_update) or force:
            coros = [self.update_area(x) for x in areas]
            if len(self._regions) == 0:
                await self._load_regions()
            coros.extend(
                [self.update_region(str(region["code"]), str(region["type"]))
                 for region in self._regions]
            )
            asyncio.gather(*coros)
            return list(self.location_cache.values())

    async def parse_response(self, response) -> list[FuelLocation]:
        """Parse response into a list of stations."""
        _LOGGER.debug("Found %s fuel stations", len(response))
        for station in response:
            site_id = f"{self.provider_name}_{station['id']}"
            if site_id in self.location_cache:
                self._update_fuel_station_prices(station, site_id)
                continue
            loc = self._parse_raw_fuel_station(station, site_id)
            self.location_cache[loc.id] = loc
            continue

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Method not used."""
