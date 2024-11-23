"""Goriva Source."""

import logging
import json
from datetime import datetime

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID,
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS
)
from pyfuelprices.sources import Source, geocode_reverse_lookup, geopyexc
from pyfuelprices.fuel import Fuel
from pyfuelprices.fuel_locations import FuelLocation

_LOGGER = logging.getLogger(__name__)

class GorivaSource(Source):
    """Goriva fuel source."""

    provider_name="goriva"
    location_cache: dict[str, FuelLocation] = {}
    _url: str = "https://goriva.si/api/v1/search/?position={LAT},{LONG}&radius={RADIUS}&franchise=&name=&o="

    async def _send_request(self, url: str, lat, long, radius) -> str:
        """Send a request to the API and return the raw response."""
        url = url.format(
            LAT=lat,
            LONG=long,
            RADIUS=radius
        )
        _LOGGER.debug("Sending HTTP request to %s with URL %s", self.provider_name, url)
        radius = (radius * 1.609344)*1000 # convert miles to m
        async with self._client_session.get(url=url) as response:
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
        data = await super().search_sites(coordinates, radius)
        return data

    async def update(self, areas=None, force=False) -> list[FuelLocation]:
        """Update hooks for the data source."""
        _LOGGER.debug("Starting update hook for %s to url %s", self.provider_name, self._url)
        self._configured_areas=[] if areas is None else areas
        self._clear_cache()
        if self.next_update <= datetime.now() or force:
            for area in self._configured_areas:
                try:
                    geocode = await geocode_reverse_lookup(
                        (area[PROP_AREA_LAT], area[PROP_AREA_LONG])
                    )
                except geopyexc.GeocoderTimedOut:
                    _LOGGER.warning("Timeout occured while geocoding area %s.",
                                    area)
                    continue
                if geocode.raw["address"]["country_code"] != "si":
                    _LOGGER.debug("Skipping area %s as not in SI.",
                                area)
                    continue
                response = json.loads(await self._send_request(
                    url=self._url,
                    radius=area[PROP_AREA_RADIUS],
                    lat=area[PROP_AREA_LAT],
                    long=area[PROP_AREA_LONG]
                ))
                await self.parse_response(response["results"])
            self.next_update = datetime.now() + self.update_interval
        return list(self.location_cache.values())

    async def parse_response(self, response) -> list[FuelLocation]:
        """Converts CMA data into fuel price mapping."""
        for location_raw in response:
            site_id = f"{self.provider_name}_{location_raw['pk']}"
            location = FuelLocation.create(
                    site_id=site_id,
                    name=location_raw['name'],
                    address=location_raw["address"],
                    brand="",
                    lat=location_raw["lat"],
                    long=location_raw["lng"],
                    available_fuels=self.parse_fuels(location_raw["prices"]),
                    postal_code=location_raw["zip_code"],
                    currency="EUR",
                    props={
                        PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                        PROP_FUEL_LOCATION_SOURCE_ID: location_raw["pk"],
                        PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                        "open_hours": location_raw["open_hours"]
                    },
                    next_update=self.next_update
                )
            if site_id not in self.location_cache:
                self.location_cache[site_id] = location
            else:
                await self.location_cache[site_id].update(location)
        return list(self.location_cache.values())

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Parses fuel data."""
        output = []
        for k in fuels:
            if fuels[k] is None:
                continue
            output.append(
                Fuel(
                    fuel_type=k,
                    cost=fuels[k],
                    props={}
                )
            )
        return output
