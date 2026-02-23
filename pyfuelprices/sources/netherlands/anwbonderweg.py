"""Official ANWB onderweg Fuel Data Source."""

# This is an official data source for Home Assistant users from Finelly
import logging

from geopy import (
    distance ,
    point  
)
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

from .const import ANWB_API_BASE, ANWB_API_FUEL_STATION

_LOGGER = logging.getLogger(__name__)
CONFIG = vol.Schema(
    {
    }
)

class ANWBOnderwegDataSource(Source):
    """Core ANWB onderweg source."""

    provider_name="ANWBOnderweg"
    location_cache: dict[str, FuelLocation] = {}
    attr_config = CONFIG

    def _build_request_url(self,lat: float, long: float, radius: float):
        """Build a valid request URL."""

        center = point.Point(lat, long)

        north = distance.distance(kilometers=radius).destination(center, 0)
        south = distance.distance(kilometers=radius).destination(center, 180)
        east = distance.distance(kilometers=radius).destination(center, 90)
        west = distance.distance(kilometers=radius).destination(center, 270)
        
        min_lat = south.latitude
        max_lat = north.latitude
        min_lon = west.longitude
        max_lon = east.longitude

        return f"{ANWB_API_BASE}&bounding-box-filter={min_lat}%2C{min_lon}%2C{max_lat}%2C{max_lon}"

    async def update_area(self, area: dict) -> bool:
        """Update a given area."""
        response = await self._client_session.get(
            url=self._build_request_url(
                lat=area[PROP_AREA_LAT],
                long=area[PROP_AREA_LONG],
                radius=area[PROP_AREA_RADIUS]
            )
        )
        if response is None:
            return False
        if not response.ok:
            _LOGGER.error("Error communicating with ANWB onderweg API.")
            return False
        await self.parse_response(await response.json())
        return True

    async def search_sites(self, coordinates, radius: float) -> list[dict]:
        """Return all available sites within the bounding-box-filter"""
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
        i = 0
        if response['value']:
            for station in response['value']:
                await self.parse_fuel_station(station)
                i+1
                if i % 100 == 1:
                    _LOGGER.debug(f"{i} stations loaded")
        return list(self.location_cache.values())

    async def parse_fuel_station(self, data: dict):
        """Parse a given fuel station and load into cache."""
        site_id = f"{self.provider_name}_{data['id']}"
        address = data.get("address")
        coordinates = data.get("coordinates")  
        loc = FuelLocation.create(
            site_id=site_id,
            name=data.get("title", None),
            address=f"{address.get("streetAddress"), address.get("city")}",
            lat=coordinates.get("latitude"),
            long=coordinates.get("longitude"),
            brand=None,
            available_fuels=self.parse_fuels(data.get("prices")),
            postal_code=f"{data.get("address").get("postalCode")}" ,
            currency="EUR",
            props={
                PROP_FUEL_LOCATION_DYNAMIC_BUILD: True,
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: data["id"]
            },
        )
        loc.next_update = self.next_update + self.update_interval
        if site_id not in self.location_cache:
            self.location_cache[site_id] = loc
        else:
            await self.location_cache[site_id].update(loc)
        return self.location_cache[site_id]

    def parse_fuels(self, fuels) -> list[Fuel]:
        retVal = []
        if fuels:
            for fuel in fuels:
                retVal.append(Fuel(fuel_type=fuel.get("fuelType"), cost=fuel.get("value")))
        return retVal
