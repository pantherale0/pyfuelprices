"""Data sources and translators for pyfuelprices."""

import logging
import json

from datetime import timedelta, datetime
from typing import final
from geopy import distance, Nominatim, location, adapters
# from sklearn.neighbors import KDTree

# import pandas as pd
import aiohttp
import reverse_geocode

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS
)
from pyfuelprices.fuel_locations import FuelLocation, Fuel
from pyfuelprices._version import __version__ as VERSION

_LOGGER = logging.getLogger(__name__)

async def geocode_reverse_lookup(coordinates: tuple) -> location.Location:
    """Reverse GeoCode lookup."""
    async with Nominatim(
        user_agent=f"pyfuelprices-{VERSION}",
        adapter_factory=adapters.AioHTTPAdapter) as geolocator:
        return await geolocator.reverse(coordinates, exactly_one=True)

def geocode_country_lookup(coordinates: tuple):
    """Reverse geocode country lookup using reverse-geocode."""
    results = reverse_geocode.search(coordinates=[coordinates])
    if len(results) > 0:
        return results[0]["country_code"]
    raise LookupError("Country not found for given coordinates.",
                      coordinates)

class Source:
    """Base source, all instances inherit this."""

    _url: str = ""
    _method: str = "GET"
    _request_body: dict | None = None
    _headers: dict = {}
    _raw_data = None
    _timeout: int = 30
    _configured_areas: list[dict] = []
    _client_session: aiohttp.ClientSession = None
    update_interval: timedelta = timedelta(days=1)
    next_update: datetime = datetime.now()
    provider_name: str = ""
    location_cache: dict[str, FuelLocation] = None
    # location_tree: KDTree

    def __init__(self,
                 update_interval: timedelta = timedelta(days=1),
                 client_session: aiohttp.ClientSession = None) -> None:
        """Start a new instance of a source."""
        self.update_interval = update_interval
        self._client_session: aiohttp.ClientSession = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self._timeout),
            headers=self._headers
        )
        if client_session is None:
            self._client_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout)
            )
        else:
            self._client_session = client_session
        if self.next_update is None:
            self.next_update = datetime.now()

    @final
    def _check_if_coord_in_area(self, coordinates) -> bool:
        """Check to see if given coordinates are in a configured area."""
        for area in self._configured_areas:
            if distance.distance(
                coordinates,
                (area[PROP_AREA_LAT], area[PROP_AREA_LONG])
            ).miles <= area[PROP_AREA_RADIUS]:
                return True
        return False

    async def get_site(self, site_id) -> FuelLocation:
        """Return an individual fuel location from the remote API."""
        return self.location_cache[site_id]

    async def search_sites(self, coordinates, radius: float) -> list[FuelLocation]:
        """Return all available sites within a given radius."""
        locations = []
        # if self.location_tree is None:
        for site in self.location_cache.values():
            if distance.distance(coordinates,
                                (
                                    site.lat,
                                    site.long
                                )).miles < radius:
                locations.append(site)
        # else:
        #     indices = self.location_tree.query([[coordinates[0], coordinates[1]]],
        #                                        k = len(self.location_cache),
        #                                        sort_results=True,
        #                                        return_distance=False).tolist()[0]
        #     for i in indices:
        #         loc = list(self.location_cache.values())[i]
        #         if distance.distance(coordinates,
        #                              (loc.lat, loc.long)
        #                              ).miles < radius:
        #             locations.append(loc)
        #         else:
        #             break
        return locations

    async def update(self, areas=None) -> list[FuelLocation]:
        """Update hooks for the data source."""
        _LOGGER.debug("Starting update hook for %s to url %s", self.provider_name, self._url)
        self._configured_areas=[] if areas is None else areas
        self._clear_cache()
        if datetime.now() > self.next_update:
            response = await self._client_session.request(
                method=self._method,
                url=self._url,
                json=self._request_body,
                headers=self._headers
            )
            _LOGGER.debug("Update request completed for %s with status %s",
                        self.provider_name, response.status)
            if response.status == 200:
                self.next_update += self.update_interval
                if "application/json" not in response.content_type:
                    return await self.parse_response(
                        response=json.loads(await response.text())
                    )
                return await self.parse_response(
                    response=await response.json()
                )
            raise UpdateFailedError(
                status=response.status,
                response=await response.text(),
                headers=response.headers
            )

    async def parse_response(self, response) -> list[FuelLocation]:
        """Parses the response from the update hook."""
        raise NotImplementedError("This function is not available for this module.")

    @final
    def _clear_cache(self):
        """Remove data for fuel stations that have not been accessed."""
        for x in range(len(self.location_cache)):
            last_access = list(self.location_cache.values())[x].last_access
            if last_access is not None:
                if last_access <= datetime.now()-timedelta(days=2):
                    if not list(self.location_cache.values())[x].props.get(
                        PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
                        False
                    ):
                        list(self.location_cache.values())[x].available_fuels = []

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Parses the fuels response from the update hook.
        This is used as part of parse_response."""
        raise NotImplementedError("This function is not available for this module.")


class UpdateFailedError(Exception):
    """Update failure exception."""

    def __init__(self, status: int, response: str, headers: dict) -> None:
        self.status = status
        self.response = response
        self.headers = headers
