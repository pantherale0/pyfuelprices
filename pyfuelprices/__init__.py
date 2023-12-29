"""The core fuel prices module."""

import logging
import asyncio

from datetime import timedelta, datetime
from geopy import distance

from pyfuelprices.sources import Source, UpdateFailedError
from pyfuelprices.sources.mapping import SOURCE_MAP, COUNTRY_MAP
from .fuel_locations import FuelLocation

_LOGGER = logging.getLogger(__name__)

class FuelPrices:
    """The base fuel prices entry class."""

    configured_sources: list[Source] = []
    fuel_locations: dict[str, FuelLocation] = {}
    configured_preload_areas: dict[str, dict[str, object]] = {}

    async def update(self):
        """Update helper to update all configured sources."""
        async def update_iteration(src: Source, preload_areas: dict[str, dict[str, object]]):
            if datetime.now() > src.next_update:
                try:
                    updated = await src.update(preload_areas=preload_areas)
                    for loc in updated:
                        if loc.id in self.fuel_locations:
                            await self.fuel_locations[loc.id].update(loc)
                        else:
                            self.fuel_locations[loc.id] = loc
                except TimeoutError:
                    _LOGGER.warning("Timeout updating data for %s, will attempt again in 30 mins",
                                    src.provider_name)
                    src.next_update += timedelta(minutes=30)
                except UpdateFailedError as err:
                    _LOGGER.warning("Error updating data for %s, response code %s: %s",
                                    src.provider_name,
                                    err.status,
                                    err.response)
                    src.next_update += timedelta(minutes=60)

        coros = [update_iteration(s, self.configured_preload_areas)
                 for s in self.configured_sources]
        await asyncio.gather(*coros)

    def get_fuel_location(self, site_id: str) -> FuelLocation:
        """Retrieve a single fuel location."""
        return self.fuel_locations.get(site_id)

    async def async_get_fuel_location(self, site_id: str) -> FuelLocation:
        """Retrieve a single fuel location (supporting dynamic parse)."""
        loc = self.get_fuel_location(site_id)
        await loc.dynamic_build_fuels()
        return loc

    def find_fuel_locations_from_point(self, point, radius: float) -> list[str]:
        """Retrieve all fuel locations from a single point."""
        _LOGGER.debug("Searching for all fuel locations at point %s with a %s mile radius.",
                      point,
                      radius)
        location_ids = []
        for site_id in self.fuel_locations:
            if distance.distance(point,
                                 (
                                    self.get_fuel_location(site_id).lat,
                                    self.get_fuel_location(site_id).long
                                )).miles < radius:
                location_ids.append(self.get_fuel_location(site_id).id)
        return location_ids

    def find_fuel_from_point(self, point, radius: float, fuel_type: str) -> dict[str, float]:
        """Retrieve the fuel cost from a single point."""
        _LOGGER.debug("Searching for fuel %s", fuel_type)
        locations = self.find_fuel_locations_from_point(point, radius)
        fuels = {}
        for loc_id in locations:
            loc = self.get_fuel_location(loc_id)
            for fuel in loc.available_fuels:
                if (fuel.fuel_type == fuel_type and
                    fuel.cost > 0.1):
                    fuels[loc.name] = fuel.cost

        return sorted(fuels.items(), key=lambda item: item[1])

    async def async_find_fuel_from_point(self,
                                                 point,
                                                 radius: float,
                                                 fuel_type: str) -> dict[str, float]:
        """Retrieve the fuel cost from a single point."""
        _LOGGER.debug("Searching for fuel %s", fuel_type)
        locations = self.find_fuel_locations_from_point(point, radius)
        fuels = {}
        for loc_id in locations:
            loc = await self.async_get_fuel_location(loc_id)
            for fuel in loc.available_fuels:
                if (fuel.fuel_type == fuel_type and
                    fuel.cost > 0.1):
                    fuels[loc.name] = fuel.cost

        return sorted(fuels.items(), key=lambda item: item[1])

    @classmethod
    def create(cls,
               enabled_sources: list[str] = None,
               update_interval: timedelta = timedelta(days=1),
               country_code: str = "",
               preload_areas: dict[str, dict[str, object]] = None
            ) -> 'FuelPrices':
        """Start an instance of fuel prices."""
        self = cls()
        self.configured_preload_areas = preload_areas
        if enabled_sources is not None:
            for src in enabled_sources:
                if str(src) not in SOURCE_MAP:
                    raise ValueError(f"Source {src} is not valid for this application.")
                self.configured_sources.append(
                    SOURCE_MAP.get(str(src))(update_interval=update_interval)
                )
        if enabled_sources is None:
            def_sources = SOURCE_MAP
            if country_code != "":
                def_sources = COUNTRY_MAP.get(country_code.upper())
            for src in def_sources:
                self.configured_sources.append(
                    SOURCE_MAP.get(str(src))(update_interval=update_interval)
                )

        return self
