"""FuelSnoop data source for Australia (QLD)."""

from datetime import datetime
import logging
import json

from geopy import distance

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_SOURCE_ID,
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS
)
from pyfuelprices.fuel_locations import FuelLocation, Fuel
from pyfuelprices.helpers import get_bounding_box
from pyfuelprices.sources import Source

from .const import FUELSNOOP_API_HEADERS, FUELSNOOP_API_SITES

_LOGGER = logging.getLogger(__name__)

class FuelSnoopSource(Source):
    """FuelSnoop data source."""
    provider_name = "fuelsnoop"
    _fuel_products: list[str] = []
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None

    async def _send_request(self, url, body):
        """Send a HTTP request to the API and return the text."""
        async with self._client_session.post(
            url,
            headers=FUELSNOOP_API_HEADERS,
            json=body) as response:
            if response.ok:
                return await response.text()
            _LOGGER.error("Error sending request to %s: %s",
                            url,
                            response)

    async def search_sites(self, coordinates, radius: float) -> list[dict]:
        """Return all available sites within a given radius."""
        # first query the API to populate cache / update data in case this data is unavailable.
        await self.update(
            areas=[{
                PROP_AREA_LAT: coordinates[0],
                PROP_AREA_LONG: coordinates[1],
                PROP_AREA_RADIUS: radius
            }],
            force=True
        )
        locations = []
        for site in self.location_cache.values():
            dist = distance.distance(coordinates,
                                 (
                                    site.lat,
                                    site.long
                                )).miles
            if dist < radius:
                locations.append({
                    **site.__dict__(),
                    "distance": dist
                })
        return locations

    async def update(self, areas=None, force=None) -> list[FuelLocation]:
        """Custom update handler to look all products."""
        self._configured_areas=[] if areas is None else areas
        if datetime.now() > self.next_update or force:
            for area in self._configured_areas:
                _LOGGER.debug("Searching FuelSnoop for FuelLocations at area %s",
                              area)
                bbox = get_bounding_box(
                    area[PROP_AREA_LAT],
                    area[PROP_AREA_LONG],
                    area[PROP_AREA_RADIUS]
                )
                response_raw = await self._send_request(
                    url=FUELSNOOP_API_SITES,
                    body={
                        "min_lng": bbox.lon_min,
                        "min_lat": bbox.lat_min,
                        "max_lng": bbox.lon_max,
                        "max_lat": bbox.lat_max,
                        "brand_names": []
                    }
                )
                if response_raw is not None:
                    await self.parse_response(json.loads(response_raw))
            self.next_update += self.update_interval
            return list(self.location_cache.values())

    async def parse_response(self, response) -> list[FuelLocation]:
        for station in response:
            await self.parse_raw_fuel_station(station=station)
        return list(self.location_cache.values())

    async def parse_raw_fuel_station(self, station) -> FuelLocation:
        """Convert an instance of a single fuel station into a FuelLocation."""
        site_id = f"{self.provider_name}_{station['id']}"
        _LOGGER.debug("Parsing FuelSnoop location ID %s", site_id)
        loc = FuelLocation.create(
            site_id=site_id,
            name=station["site_name"],
            address=station['address'],
            lat=station['lat'],
            long=station['lng'],
            brand=station['brand_name'],
            available_fuels=self.parse_fuels(station["prices"]),
            postal_code=station['postcode'],
            currency="AUD",
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
            if f["price"] > 999:
                continue # ignore this fuel as not available at this stn
            output.append(Fuel(
                fuel_type=k,
                cost=f["price"],
                props=f
            ))
        return output
