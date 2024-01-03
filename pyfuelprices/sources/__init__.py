"""Data sources and translators for pyfuelprices."""

import logging
import json

from datetime import timedelta, datetime
from typing import final
from geopy import distance

import aiohttp

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS
)
from pyfuelprices.fuel_locations import FuelLocation, Fuel

_LOGGER = logging.getLogger(__name__)

class Source:
    """Base source, all instances inherit this."""

    _url: str = ""
    _method: str = "GET"
    _request_body: dict | None = None
    _headers: dict = {}
    _raw_data = None
    _timeout: int = 30
    _configured_areas: list[dict] = []
    update_interval: timedelta | None = None
    next_update: datetime | None = None
    provider_name: str = ""
    location_cache: dict[str, FuelLocation] = {}

    def __init__(self,
                 update_interval: timedelta = timedelta(days=1)) -> None:
        """Start a new instance of a source."""
        self.update_interval = update_interval
        self._client_session: aiohttp.ClientSession = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self._timeout),
            headers=self._headers
        )
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
        for site in self.location_cache.values():
            if distance.distance(coordinates,
                                 (
                                    site.lat,
                                    site.long
                                )).miles < radius:
                locations.append(site)
        return locations

    async def update(self, areas=None) -> list[FuelLocation]:
        """Update hooks for the data source."""
        _LOGGER.debug("Starting update hook for %s to url %s", self.provider_name, self._url)
        self._configured_areas=[] if areas is None else areas
        self._clear_cache()
        if datetime.now() > self.next_update:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout),
                headers=self._headers
            ) as session:
                response = await session.request(
                    method=self._method,
                    url=self._url,
                    json=self._request_body
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
