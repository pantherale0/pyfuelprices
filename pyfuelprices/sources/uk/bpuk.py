"""BP UK dataprovider."""

from pyfuelprices.const import DESKTOP_USER_AGENT
from pyfuelprices.fuel import Fuel
from pyfuelprices.sources.uk import CMAParser, FuelLocation

class BpUKSource(CMAParser):
    """BP UK uses the CMA parser."""

    _url = "https://www.bp.com/en_gb/united-kingdom/home/fuelprices/fuel_prices_data.json"
    provider_name = "bpuk"
    _headers = {
        "User-Agent": DESKTOP_USER_AGENT
    }
    _timeout = 60
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
