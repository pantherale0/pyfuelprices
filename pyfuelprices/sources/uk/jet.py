"""JET UK module."""

from pyfuelprices.sources import Source
from pyfuelprices.sources.uk import CMAParserMixIn, FuelLocation

class JetUKSource(CMAParserMixIn, Source):
    """JET uses the CMA parser."""

    country_code = "GB"

    _url = "https://jetlocal.co.uk/fuel_prices_data.json"
    provider_name = "jet"
    _timeout = 10
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
