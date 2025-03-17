"""Official Finelly Fuel Data Source."""

# This is an official data source for Home Assistant users from Finelly
import asyncio
import logging
from datetime import datetime, timedelta

import voluptuous as vol

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_DYNAMIC_BUILD,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_SOURCE_ID,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS
)
from pyfuelprices.build_data import (
    FINELLY_URL
)
from pyfuelprices.fuel_locations import FuelLocation, Fuel
from pyfuelprices.enum import SupportsConfigType
from pyfuelprices.sources import Source

from .const import FINELLY_FUEL_API

_LOGGER = logging.getLogger(__name__)
CONFIG = vol.Schema(
    {
        vol.Required("USER_ID"): str
    }
)

class FinellyDataSource(Source):
    """Core Finelly source."""

    provider_name="finelly"
    location_cache: dict[str, FuelLocation] = {}
    update_interval = timedelta(hours=12)
    attr_config_type = SupportsConfigType.REQUIRES_ONLY
    attr_config = CONFIG

    def _build_request_url(self, lat: float, long: float, radius: float):
        """Build a valid request URL."""
        return FINELLY_FUEL_API.format(
            FURL=FINELLY_URL,
            LAT=lat,
            LONG=long,
            RAD=radius,
            USER=self.configuration["USER_ID"]
        )

    async def update_area(self, area: dict):
        """Update a given area."""
        response = await self._client_session.get(
            url=self._build_request_url(
                lat=area[PROP_AREA_LAT],
                long=area[PROP_AREA_LONG],
                radius=area[PROP_AREA_RADIUS]
            )
        )
        if response is None:
            return
        if not response.ok:
            _LOGGER.error("Error communicating with Finelly API.")
            return
        await self.parse_response(await response.json())

    async def update(self, areas=None, force=False):
        """Update Finelly areas."""
        self._configured_areas = areas or []
        self._clear_cache()
        if self.next_update > datetime.now() and not force:
            return
        coros = [
            self.update_area(a) for a in self._configured_areas
        ]
        await asyncio.gather(*coros)
        return list(self.location_cache.values())

    async def search_sites(self, coordinates, radius: float) -> list[dict]:
        """Return all available sites within a given radius."""
        # first query the API to populate cache / update data in case this data is unavailable.
        data = await super().search_sites(coordinates, radius)
        if len(data)>0:
            return data
        await self.update(
            areas=[
                {
                    PROP_AREA_LAT: coordinates[0],
                    PROP_AREA_LONG: coordinates[1],
                    PROP_AREA_RADIUS: radius
                }
            ],
            force=True
        )
        return await super().search_sites(coordinates, radius)

    async def parse_response(self, response: dict):
        """Parse response data."""
        for station in response:
            await self.parse_fuel_station(station)
        return list(self.location_cache.values())

    async def parse_fuel_station(self, data: dict):
        """Parse a given fuel station and load into cache."""
        site_id = f"{self.provider_name}_{data['id']}"
        _LOGGER.debug("Parsing Finelly location ID %s", site_id)
        loc = FuelLocation.create(
            site_id=site_id,
            name=data["name"],
            address="",
            lat=data["location"]["latitude"],
            long=data["location"]["longitude"],
            brand=data["brand"],
            available_fuels=self.parse_fuels(data["petrolPrices"]),
            postal_code="",
            currency="NZD",
            props={
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                PROP_FUEL_LOCATION_DYNAMIC_BUILD: False,
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: data["id"]
            }
        )
        loc.next_update = self.next_update + self.update_interval
        if site_id not in self.location_cache:
            self.location_cache[site_id] = loc
        else:
            await self.location_cache[site_id].update(loc)
        return self.location_cache[site_id]

    def parse_fuels(self, fuels: list[dict]):
        """Parse fuels."""
        return [
            Fuel(
                fuel_type=x.get("petrolType"),
                cost=x.get("price"),
                props=x
            ) for x in fuels
        ]
