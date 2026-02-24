"""SGN Retail UK dataprovider."""

from pyfuelprices.sources import Source
from pyfuelprices.sources.uk import CMAParserMixIn, FuelLocation

class SgnRetailUKSource(CMAParserMixIn, Source):
    """SGN Retail UK uses the CMA parser."""

    country_code = "GB"

    _url = "https://www.sgnretail.uk/files/data/SGN_daily_fuel_prices.json"
    provider_name = "sgnretail"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
