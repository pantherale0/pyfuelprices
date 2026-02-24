"""Motor Fuel Group UK dataprovider."""

from pyfuelprices.sources import Source
from pyfuelprices.sources.uk import CMAParserMixIn, FuelLocation

class MotorFuelGroupUKSource(CMAParserMixIn, Source):
    """Motor Fuel Group UK uses the CMA parser."""

    country_code = "GB"

    _url = "https://fuel.motorfuelgroup.com/fuel_prices_data.json"
    provider_name = "motorfuelgroup"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
