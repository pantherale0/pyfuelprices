"""Karan Retail Ltd dataprovider."""

from pyfuelprices.sources import Source
from pyfuelprices.sources.uk import CMAParserMixIn, FuelLocation

class KaranRetailSource(CMAParserMixIn, Source):
    """Karan Retail Ltd uses the CMA parser."""

    country_code = "GB"

    _url = "https://api.krl.live/integration/live_price/krl"
    provider_name = "karanretail"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
