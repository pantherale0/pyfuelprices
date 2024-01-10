"""The core fuel prices module."""

import logging
import asyncio

from datetime import timedelta

import aiohttp

from pyfuelprices.sources import Source, geocode_country_lookup
from pyfuelprices.sources.mapping import SOURCE_MAP, COUNTRY_MAP
from .const import PROP_FUEL_LOCATION_SOURCE
from .fuel_locations import FuelLocation

_LOGGER = logging.getLogger(__name__)

class FuelPrices:
    """The base fuel prices entry class."""

    configured_sources: dict[str, Source] = {}
    configured_areas: list[dict] = []
    _accessed_sites: dict[str, str] = {}
    client_session: aiohttp.ClientSession = None

    async def update(self):
        """Main data fetch / update handler."""
        async def update_src(s: Source, a: list[dict]):
            """Update source."""
            try:
                async with asyncio.Semaphore(4):
                    await s.update(areas=a)
            except TimeoutError as err:
                _LOGGER.warning("Timeout updating %s: %s", s.provider_name, err)
        coros = [update_src(s, self.configured_areas) for s in self.configured_sources.values()]
        await asyncio.gather(*coros)

    async def get_fuel_location(self, site_id: str, source_id: str) -> FuelLocation:
        """Retrieve a single fuel location (supporting dynamic parse)."""
        if site_id not in self._accessed_sites:
            self._accessed_sites[site_id] = source_id
        return await self.configured_sources[source_id].get_site(site_id)

    async def find_fuel_locations_from_point(self,
                                       coordinates,
                                       radius: float,
                                       source_id: str = "") -> list[FuelLocation]:
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
        geocoded = geocode_country_lookup(coordinates)
        if geocoded not in COUNTRY_MAP:
            raise ValueError("No data source exists for the given coordinates.", geocoded)
        locations = []
        for src in COUNTRY_MAP.get(geocoded, []):
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
                             source_id: str = "") -> dict[str, float]:
        """Retrieve the fuel cost from a single point."""
        async def dynamic_build(l: FuelLocation):
            """Function for asyncio to retrieve fuels quickly."""
            async with asyncio.Semaphore(5):
                await l.dynamic_build_fuels()

        _LOGGER.debug("Searching for fuel %s", fuel_type)
        locations = await self.find_fuel_locations_from_point(
            coordinates,
            radius,
            source_id)
        coros = [dynamic_build(l) for l in locations]
        await asyncio.gather(*coros)
        fuels = {}
        for loc in locations:
            if loc.id not in self._accessed_sites:
                self._accessed_sites[loc.id] = loc.props[PROP_FUEL_LOCATION_SOURCE]
            for fuel in loc.available_fuels:
                if (fuel.fuel_type == fuel_type) and (
                    fuel.cost > 0
                ):
                    fuels[loc.name] = fuel.cost

        return sorted(fuels.items(), key=lambda item: item[1])

    @classmethod
    def create(cls,
               enabled_sources: list[str] = None,
               update_interval: timedelta = timedelta(days=1),
               country_code: str = "",
               configured_areas: list[dict] = None,
               timeout: timedelta = timedelta(seconds=30)
            ) -> 'FuelPrices':
        """Start an instance of fuel prices."""
        self = cls()
        self.configured_areas = configured_areas
        self.client_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                use_dns_cache=True,
                ttl_dns_cache=360
            ),
            timeout=aiohttp.ClientTimeout(
                total=timeout.seconds
            )
        )
        if enabled_sources is not None:
            for src in enabled_sources:
                if str(src) not in SOURCE_MAP:
                    raise ValueError(f"Source {src} is not valid for this application.")
                self.configured_sources[src] = (
                    SOURCE_MAP.get(str(src))(update_interval=update_interval,
                                             client_session=self.client_session)
                )
        if enabled_sources is None:
            def_sources = {}
            if country_code != "":
                def_sources = COUNTRY_MAP.get(country_code.upper(), [])
            for src in def_sources:
                self.configured_sources[src] = (
                    SOURCE_MAP.get(str(src))(update_interval=update_interval,
                                             client_session=self.client_session)
                )

        return self
