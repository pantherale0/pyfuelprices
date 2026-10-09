"""Data sources and translators for pyfuelprices."""

import asyncio
import logging
from datetime import timedelta, datetime
from typing import final
from geopy import (
    distance
)
import aiohttp

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS
)
from pyfuelprices.fuel_locations import FuelLocation, Fuel
from pyfuelprices.enum import SupportsConfigType
from pyfuelprices.schemas import SOURCE_BASE_CONFIG

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
    _session: aiohttp.ClientSession | None = None
    _owns_session: bool = True
    update_interval: timedelta = None
    next_update: datetime = datetime.now()
    provider_name: str = ""
    location_cache: dict[str, FuelLocation] = None
    configuration: dict | None = None
    attr_config_type: SupportsConfigType = SupportsConfigType.NONE
    attr_config = SOURCE_BASE_CONFIG
    country_code: str | list[str]
    enabled: bool = True
    available_for_setup: bool = True
    auto_country_mapping: bool = True

    def __init__(self,
                 configured_areas: list[dict] = None,
                 update_interval: timedelta = timedelta(days=1),
                 client_session: aiohttp.ClientSession = None,
                 configuration: dict | None = None) -> None:
        """Start a new instance of a source."""
        self._configured_areas = configured_areas or []
        if self.update_interval is None:
            if update_interval is not None:
                self.update_interval = update_interval
            else:
                self.update_interval = timedelta(days=1)
        # Must be per instance: a class-level dict is shared by every FuelPrices
        # instance, so stale sources survive integration reloads.
        self.location_cache = {}
        self._session = client_session
        self._owns_session = client_session is None
        if self.next_update is None:
            self.next_update = datetime.now()
        self._validate_config(configuration)
        self.configuration = configuration

    @property
    def _client_session(self) -> aiohttp.ClientSession:
        """Return a usable client session, recreating it if owned and closed."""
        if self._session is None or self._session.closed:
            if not self._owns_session:
                raise SessionClosedError(self.provider_name)
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout)
            )
        return self._session

    def attach_session(self, client_session: aiohttp.ClientSession) -> None:
        """Use an externally managed client session."""
        self._session = client_session
        self._owns_session = False

    async def close(self) -> None:
        """Close the client session if this source created it."""
        if self._owns_session and self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

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
        await self.location_cache[site_id].dynamic_build_fuels()
        return self.location_cache[site_id]

    async def search_sites(self, coordinates, radius: float) -> list[dict]:
        """Return all available sites within a given radius."""
        locations = []
        for site in self.location_cache.values():
            dist = distance.distance(coordinates,
                                (
                                    site.lat,
                                    site.long
                                )).miles
            if dist < radius:
                await site.dynamic_build_fuels()
                locations.append(
                    {
                        **site.__dict__,
                        "distance": dist
                    }
                )
        return locations

    async def update_area(self, area: dict) -> bool:
        """Update a given area."""
        raise NotImplementedError("Not implemented.")

    async def update(self, areas=None, force=False) -> list[FuelLocation]:
        """Update hooks for the data source."""
        _LOGGER.debug("Starting update hook for %s to url %s", self.provider_name, self._url)
        areas = areas or self._configured_areas
        self._clear_cache()
        if self.next_update > datetime.now() and not force:
            _LOGGER.debug("Ignoring update request")
            return
        coros = [
            self.update_area(a) for a in areas
        ]
        results = await asyncio.gather(*coros, return_exceptions=True)
        for result in results:
            if isinstance(result, SessionClosedError):
                raise result
            if isinstance(result, Exception):
                _LOGGER.error("Update area failed for %s: %r", self.provider_name, result)
        self.next_update = datetime.now() + self.update_interval
        return list(self.location_cache.values())

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

    @final
    def _validate_config(self, configuration: dict):
        """Validate a given config."""
        if self.attr_config_type == SupportsConfigType.NONE:
            return True
        if self.attr_config is None:
            return True
        self.attr_config(configuration)

class UpdateFailedError(Exception):
    """Update failure exception."""

    def __init__(self, status: int, response: str, headers: dict, service: str) -> None:
        self.status = status
        self.response = response
        self.headers = headers
        self.service = service

class ServiceBlocked(UpdateFailedError):
    """Service Blocked exception."""

class SessionClosedError(RuntimeError):
    """The externally provided client session has been closed.

    The owner of the session must create a new FuelPrices instance (or call
    FuelPrices.attach_session) with a live session.
    """

    def __init__(self, service: str) -> None:
        super().__init__(f"Client session for {service} is closed")
        self.service = service
