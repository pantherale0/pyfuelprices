"""UK Fuel Sources and parsers."""

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID
)
from pyfuelprices.sources import Source #, KDTree, pd
from pyfuelprices.fuel import Fuel
from pyfuelprices.fuel_locations import FuelLocation

class CMAParser(Source):
    """This parser is specific for the scheme by the CMA."""

    location_cache: dict[str, FuelLocation] = {}
    # location_tree: KDTree

    async def parse_response(self, response) -> list[FuelLocation]:
        """Converts CMA data into fuel price mapping."""
        # _df_columns = ["lat", "long"]
        # _df_data = []
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
                    }
                )
            if site_id not in self.location_cache:
                self.location_cache[site_id] = location
                # _df_data.append([location.lat, location.long])
            else:
                self.location_cache[site_id].update(location)
        # _df = pd.DataFrame(_df_data, columns=_df_columns)
        # self.location_tree = KDTree(_df[["lat", "long"]].values, metric="euclidean")
        return list(self.location_cache.values())

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
