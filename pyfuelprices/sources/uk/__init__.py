"""UK Fuel Sources and parsers."""

from pyfuelprices.sources import Source
from pyfuelprices.fuel import Fuel
from pyfuelprices.fuel_locations import FuelLocation

class CMAParser(Source):
    """This parser is specific for the scheme by the CMA."""

    def parse_response(self, response) -> list[FuelLocation]:
        """Converts CMA data into fuel price mapping."""
        fuel_locations = []
        for location_raw in response["stations"]:
            location = FuelLocation.create(
                site_id=location_raw["site_id"],
                name="",
                address=location_raw["address"],
                brand=location_raw["brand"],
                lat=location_raw["location"]["latitude"],
                long=location_raw["location"]["longitude"],
                available_fuels=self.parse_fuels(location_raw["prices"]),
                postal_code=location_raw["postcode"]
            )
            location.currency = "GBP"
            # There is no name for fuel stations for this data so build one instead
            location.name = f"{location.brand} {location.postal_code}"
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
