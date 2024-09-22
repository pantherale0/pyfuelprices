"""Karan Retail Ltd dataprovider."""

from pyfuelprices.sources.uk import CMAParser, FuelLocation

class KaranRetailSource(CMAParser):
    """Karan Retail Ltd uses the CMA parser."""

    _url = "https://api2.krlmedia.com/integration/live_price/krl"
    provider_name = "karanretail"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
