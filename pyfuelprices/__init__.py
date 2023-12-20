"""The core fuel prices module."""

import logging
import asyncio

from datetime import timedelta
from geopy import distance

from pyfuelprices.sources import Source, UpdateFailedError
from pyfuelprices.sources.mapping import SOURCE_MAP
from .fuel_locations import FuelLocation

_LOGGER = logging.getLogger(__name__)

class FuelPrices:
    """The base fuel prices entry class."""

    configured_sources: list[Source] = []
    fuel_locations: list[FuelLocation] = []
    _discovered_sites: list = []

    async def update(self):
        """Update helper to update all configured sources."""
        async def update_iteration(src: Source):
            try:
                updated = await src.update()
                for loc in updated:
                    if loc.id in self._discovered_sites:
                        self.get_fuel_location(loc.id).update(loc)
                    else:
                        self.fuel_locations.append(loc)
                        self._discovered_sites.append(loc.id)
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
            except Exception as err:
                _LOGGER.error("%s", err)
                src.next_update += timedelta(minutes=60)

        coros = [update_iteration(s) for s in self.configured_sources]
        await asyncio.gather(*coros)

    def get_fuel_location(self, site_id: str) -> FuelLocation:
        """Retrieve a single fuel location."""
        for loc in self.fuel_locations:
            if loc.id == site_id:
                return loc
        raise ValueError(f"No site has been discovered for {site_id}.")

    def find_fuel_locations_from_point(self, point, radius: float) -> list[str]:
        """Retrieve all fuel locations from a single point."""
        _LOGGER.debug("Searching for all fuel locations at point %s with a %s mile radius.",
                      point,
                      radius)
        location_ids = []
        for fuel_location in self.fuel_locations:
            if distance.distance(point, (fuel_location.lat, fuel_location.long)).miles < radius:
                location_ids.append(fuel_location.id)
        return location_ids

    def find_fuel_from_point(self, point, radius: float, fuel_type: str) -> dict[str, float]:
        """Retrieve the fuel cost from a single point."""
        _LOGGER.debug("Searching for fuel %s", fuel_type)
        locations = self.find_fuel_locations_from_point(point, radius)
        fuels = {}
        for loc_id in locations:
            loc = self.get_fuel_location(loc_id)
            for fuel in loc.available_fuels:
                if fuel.fuel_type == fuel_type:
                    fuels[loc.name] = fuel.cost

        return sorted(fuels.items(), key=lambda item: item[1])

    @classmethod
    def create(cls,
               enabled_sources: list[str] = None,
               update_interval: timedelta = timedelta(days=1)
            ) -> 'FuelPrices':
        """Start an instance of fuel prices."""
        self = cls()
        if enabled_sources is not None:
            for src in enabled_sources:
                if str(src) not in SOURCE_MAP:
                    raise ValueError(f"Source {src} is not valid for this application.")
                self.configured_sources.append(
                    SOURCE_MAP.get(str(src))(update_interval=update_interval)
                )
        else:
            for src in SOURCE_MAP:
                self.configured_sources.append(
                    SOURCE_MAP.get(str(src))(update_interval=update_interval)
                )

        return self
