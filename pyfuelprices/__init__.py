"""The core fuel prices module."""

import logging
import asyncio

from datetime import timedelta

import aiohttp

from pyfuelprices.sources import (
    Source,
    geocode_reverse_lookup,
    UpdateFailedError
)
from pyfuelprices.sources.mapping import SOURCE_MAP, COUNTRY_MAP, FULL_COUNTRY_MAP
from .const import PROP_FUEL_LOCATION_SOURCE
from .enum import SupportsConfigType
from .fuel_locations import FuelLocation
from .schemas import BASE_CONFIG_SCHEMA

_LOGGER = logging.getLogger(__name__)

class FuelPrices:
    """The base fuel prices entry class."""

    configured_sources: dict[str, Source] = {}
    configured_areas: list[dict] = []
    _global_config: dict = {}
    _accessed_sites: dict[str, str] = {}
    client_session: aiohttp.ClientSession = None
    _semaphore: asyncio.Semaphore = asyncio.Semaphore(4)
    async def update(self, force: bool=False):
        """Main data fetch / update handler."""
        async def update_src(s: Source, a: list[dict], f: bool):
            """Update source."""
            try:
                async with self._semaphore:
                    await s.update(areas=a, force=f)
            except TimeoutError as err:
                _LOGGER.warning("Timeout updating %s: %s", s.provider_name, err)
            except (ValueError, TypeError) as err:
                _LOGGER.exception(err)
        coros = [
            update_src(s, self.configured_areas, force) for s in self.configured_sources.values()
        ]
        exceptions = await asyncio.gather(*coros, return_exceptions=True)
        for exc in exceptions:
            if isinstance(exc, Exception):
                raise UpdateExceptionGroup([x for x in exceptions if isinstance(x, Exception)])

    async def get_fuel_location(self, site_id: str, source_id: str) -> FuelLocation:
        """Retrieve a single fuel location (supporting dynamic parse)."""
        if site_id not in self._accessed_sites:
            self._accessed_sites[site_id] = source_id
        return await self.configured_sources[source_id].get_site(site_id)

    async def find_fuel_locations_from_point(self,
                                       coordinates,
                                       radius: float,
                                       source_id: str = "") -> list[dict]:
        """Retrieve all fuel locations from a single point."""
        _LOGGER.debug("Searching for all fuel locations at point %s with a %s "
                      "mile radius for source %s.",
                      coordinates,
                      radius,
                      source_id if source_id != "" else "any")
        if source_id != "":
            return await self.configured_sources[source_id].search_sites(
                coordinates=coordinates,
                radius=radius
            )
        geocoded = (await geocode_reverse_lookup(coordinates)).raw['address']['country_code']
        if geocoded.upper() not in FULL_COUNTRY_MAP:
            raise ValueError("No data source exists for the given coordinates.", geocoded)
        locations = []
        for src in FULL_COUNTRY_MAP.get(geocoded.upper(), []):
            if src in self.configured_sources:
                locations.extend(await self.configured_sources[src].search_sites(
                    coordinates=coordinates,
                    radius=radius
                ))
        return locations

    async def find_fuel_from_point(self,
                             coordinates,
                             radius: float,
                             fuel_type: str,
                             source_id: str = "") -> list[dict]:
        """Retrieve the fuel cost from a single point."""
        async def dynamic_build(l: dict):
            """Function for asyncio to retrieve fuels quickly."""
            async with self._semaphore:
                await self.get_fuel_location(
                    l["id"],
                    str(l["props"]["source"]).lower()
                )

        _LOGGER.debug("Searching for fuel %s", fuel_type)
        locations = await self.find_fuel_locations_from_point(
            coordinates,
            radius,
            source_id)
        coros = [dynamic_build(l) for l in locations]
        await asyncio.gather(*coros)
        fuels: list = []
        for loc in locations:
            if loc["id"] not in self._accessed_sites:
                self._accessed_sites[loc["id"]] = loc["props"][PROP_FUEL_LOCATION_SOURCE]
            for fuel in loc["available_fuels"]:
                if (fuel == fuel_type) and (
                    loc["available_fuels"][fuel] > 0
                ):
                    fuels.append({
                        **loc,
                        "cost": loc["available_fuels"][fuel],
                        "distance": loc["distance"]
                    })
        return sorted(fuels, key=lambda item: item["cost"])

    @staticmethod
    def get_source_config_schema(source_shortcode: str):
        """Return the config schema for a given source."""
        if source_shortcode not in SOURCE_MAP:
            raise ValueError(f"Source {source_shortcode} not found")
        return SOURCE_MAP[source_shortcode][0].attr_config

    @staticmethod
    def source_config_type(source_shortcode: str) -> SupportsConfigType:
        """Return the config type of a given source."""
        if source_shortcode not in SOURCE_MAP:
            raise ValueError(f"Source {source_shortcode} not found")
        return SOURCE_MAP[source_shortcode][0].attr_config_type

    @staticmethod
    def source_requires_config(source_shortcode: str) -> bool:
        """Return true if the source requires config before using."""
        return (
            FuelPrices.source_config_type(source_shortcode) in
            [SupportsConfigType.REQUIRES_AND_OPTIONAL, SupportsConfigType.REQUIRES_ONLY]
        )

    @classmethod
    def create(cls,
               client_session = None,
               configuration = None,
            ) -> 'FuelPrices':
        """Start an instance of fuel prices."""
        self = cls()
        if configuration is None:
            configuration = {}
        BASE_CONFIG_SCHEMA(configuration)
        self.configured_areas = configuration.get("areas")
        enabled_sources = list(configuration.get("providers", {}).keys())
        if client_session is not None:
            self.client_session = client_session
        else:
            self.client_session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(
                    use_dns_cache=True,
                    ttl_dns_cache=360
                ),
                timeout=aiohttp.ClientTimeout(
                    total=configuration.get("timeout", 30)
                )
            )

        if enabled_sources is None:
            enabled_sources=COUNTRY_MAP.get(configuration.get("country_code", "").upper(), [])

        for src in enabled_sources:
            if src not in SOURCE_MAP:
                _LOGGER.error("Source %s is not valid for this application.", src)
                continue
            if SOURCE_MAP.get(str(src))[1] == 0:
                _LOGGER.error("Source %s has been disabled.", src)
                continue
            if ((cls.source_config_type(src) == SupportsConfigType.REQUIRES_ONLY) or (
                cls.source_config_type(src) == SupportsConfigType.REQUIRES_AND_OPTIONAL
            )) and src not in configuration["providers"]:
                _LOGGER.error("Source %s is not available, not configured.", src)
                continue
            self.configured_sources[src] = (
                SOURCE_MAP.get(src)[0](
                    update_interval=timedelta(hours=configuration.get(
                        "update_interval", 24
                    )),
                    client_session=self.client_session,
                    configuration=configuration["providers"].get(src, {}))
                )
        self._global_config = configuration.get("global", {})
        return self

class UpdateExceptionGroup(Exception):
    """A group of exceptions."""
    def __init__(self, exceptions: list[Exception]):
        self._excs = exceptions

    @property
    def failed_providers(self) -> dict:
        """Failed providers."""
        errors = {}
        for exc in self._excs:
            if isinstance(exc, UpdateFailedError):
                errors[exc.service] = exc.status
        return errors

    @property
    def exception_list(self) -> list[Exception]:
        """A list of other exceptions."""
        return [
            x for x in self._excs if not isinstance(x, UpdateFailedError)
        ]
