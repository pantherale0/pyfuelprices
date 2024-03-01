"""UK Fuel Sources and parsers."""

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID
)
from pyfuelprices.sources import Source
from pyfuelprices.fuel import Fuel
from pyfuelprices.fuel_locations import FuelLocation

class CMAParser(Source):
    """This parser is specific for the scheme by the CMA."""

    location_cache: dict[str, FuelLocation] = {}

    async def parse_response(self, response) -> list[FuelLocation]:
        """Converts CMA data into fuel price mapping."""
        for location_raw in response["stations"]:
            site_id = f"{self.provider_name}_{location_raw['site_id']}"
            location = FuelLocation.create(
                    site_id=site_id,
                    name=f"{location_raw['brand']} {location_raw['postcode']}",
                    address=location_raw["address"],
                    brand=location_raw["brand"],
                    lat=location_raw["location"]["latitude"],
                    long=location_raw["location"]["longitude"],
                    available_fuels=self.parse_fuels(location_raw["prices"]),
                    postal_code=location_raw["postcode"],
                    currency="GBP",
                    props={
                        PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                        PROP_FUEL_LOCATION_SOURCE_ID: location_raw["site_id"],
                        PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True
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
        f_list = []
        for f_type in fuels:
            if fuels[f_type] is not None:
                if fuels[f_type] > 10000:
                    fuels[f_type] = round(fuels[f_type]/100, 1)
                if fuels[f_type] > 1000:
                    fuels[f_type] = round(fuels[f_type]/10, 1)
                if fuels[f_type] < 100:
                    fuels[f_type] = round(fuels[f_type]*100, 1)
            f_list.append(Fuel(
                fuel_type=f_type,
                cost=fuels[f_type],
                props={}
            ))
        return f_list
