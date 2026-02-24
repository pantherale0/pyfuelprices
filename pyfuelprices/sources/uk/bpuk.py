"""BP UK dataprovider."""

from pyfuelprices.sources import Source
from pyfuelprices.const import DESKTOP_USER_AGENT
from pyfuelprices.fuel import Fuel
from pyfuelprices.sources.uk import CMAParserMixIn, FuelLocation

class BpUKSource(CMAParserMixIn, Source):
    """BP UK uses the CMA parser."""

    country_code = "GB"

    _url = "https://www.bp.com/en_gb/united-kingdom/home/fuelprices/fuel_prices_data.json"
    provider_name = "bpuk"
    _headers = {
        "User-Agent": DESKTOP_USER_AGENT
    }
    _timeout = 60
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
