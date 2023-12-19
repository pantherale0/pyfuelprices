"""Asda UK module."""

import logging

from pyfuelprices.fuel_locations import FuelLocation, Fuel
from pyfuelprices.sources import Source

_LOGGER = logging.getLogger(__name__)

class AsdaUKSource(Source):
    """The main source."""

    _url = "https://storelocator.asda.com/fuel_prices_data.json"
    provider_name = "asda"
    _timeout = 10

    def parse_response(self, response) -> list[FuelLocation]:
        """Converts the esso data into fuel price mapping."""
        fuel_locations = []
        for location_raw in response["stations"]:
            location = FuelLocation()
            location.id = location_raw["site_id"]
            location.address = location_raw["address"]
            location.brand = location_raw["brand"]
            location.lat = location_raw["location"]["latitude"]
            location.long = location_raw["location"]["longitude"]
            location.available_fuels = self.parse_fuels(location_raw["prices"])
            fuel_locations.append(location)
        return fuel_locations

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Parses fuel data."""
        f_list = []
        for f_type in fuels:
            f_list.append(Fuel(
                fuel_type=f_type,
                cost=fuels[f_type],
                props={}
            ))
        return f_list
