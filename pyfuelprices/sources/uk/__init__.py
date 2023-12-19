"""UK Fuel Sources and parsers."""

from pyfuelprices.sources import Source
from pyfuelprices.fuel import Fuel
from pyfuelprices.fuel_locations import FuelLocation

class CMAParser(Source):
    """This parser is specific for the scheme by the CMA."""

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
