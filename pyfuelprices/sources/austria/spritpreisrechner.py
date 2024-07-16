"""Austria spritpreisrechner data source."""

from datetime import datetime

import logging
import json

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_SOURCE_ID,
    DESKTOP_USER_AGENT
)
from pyfuelprices.fuel_locations import FuelLocation, Fuel
from pyfuelprices.sources import Source

_LOGGER = logging.getLogger(__name__)

CONST_API_BASE = "https://www.spritpreisrechner.at/api"
CONST_API_SEARCH_REGIONS = (
    f"{CONST_API_BASE}/search/gas-stations/by-region?"
    "code={REG_CODE}&fuelType={FUEL_TYPE}&includeClosed=true&type={REG_TYPE}")
CONST_API_GET_REGIONS = (
    f"{CONST_API_BASE}/regions"
)
CONST_FUELS = ["DIE", "SUP", "GAS"]

class SpripreisrechnerATSource(Source):
    """Data source for spritpreisrechner."""
    provider_name = "spritpreisrechner"
    _headers = {
        "User-Agent": DESKTOP_USER_AGENT
    }
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
    _regions = []

    async def _send_request(self, url):
        """Send a HTTP request to the API."""
        async with self._client_session.get(
            url,
            headers=self._headers
        ) as response:
            if response.ok:
                return await response.text()
            _LOGGER.error("Error sending request to %s: %s",
                            url,
                            response)

    async def _load_regions(self):
        """Load regions into memory."""
        self._regions = json.loads(
            await self._send_request(CONST_API_GET_REGIONS)
        )

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
            available_fuels=[Fuel(
                fuel_type=station["prices"][0]["label"],
                cost=station["prices"][0]["amount"],
                props=station["prices"][0]
            )],
            postal_code=station["location"]["postalCode"],
            currency="EUR",
            props={
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: station["id"],
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                "data": station
            }
        )
        loc.next_update = self.next_update + self.update_interval
        return loc

    def _update_fuel_station_prices(self, station, site_id):
        """Internal method to update station prices."""
        fuel = station["prices"][0]
        try:
            self.location_cache[site_id].get_fuel(fuel["label"]).update(
                fuel_type=fuel["label"],
                cost=fuel["amount"],
                props=fuel
            )
        except ValueError:
            self.location_cache[site_id].available_fuels.append(
                Fuel(
                    fuel_type=fuel["label"],
                    cost=fuel["amount"],
                    props=fuel
                )
            )
        self.location_cache[site_id].last_updated = datetime.now()
        self.location_cache[site_id].next_update = (
            self.next_update + self.update_interval
        )

    async def update(self, areas=None, force=None) -> list[FuelLocation]:
        """Custom update handler to query each region."""
        if datetime.now() > self.next_update:
            if len(self._regions) == 0:
                await self._load_regions()
            for region in self._regions:
                for fuel in CONST_FUELS:
                    url = CONST_API_SEARCH_REGIONS.format(
                        REG_CODE=str(region["code"]),
                        FUEL_TYPE=fuel,
                        REG_TYPE=str(region["type"])
                    )
                    response_raw = json.loads(await self._send_request(url))
                    for station in response_raw:
                        site_id = f"{self.provider_name}_{station['id']}"
                        if site_id in self.location_cache:
                            self._update_fuel_station_prices(station, site_id)
                            continue
                        loc = self._parse_raw_fuel_station(station, site_id)
                        self.location_cache[loc.id] = loc
                        continue
            return list(self.location_cache.values())

    async def parse_response(self, response) -> list[FuelLocation]:
        """Method not used."""

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Method not used."""
