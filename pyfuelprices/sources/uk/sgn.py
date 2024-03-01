"""SGN Retail UK dataprovider."""

from pyfuelprices.fuel import Fuel
from pyfuelprices.sources.uk import CMAParser, FuelLocation

class SgnRetailUKSource(CMAParser):
    """SGN Retail UK uses the CMA parser."""

    _url = "https://www.sgnretail.uk/files/data/SGN_daily_fuel_prices.json"
    provider_name = "sgnretail"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
