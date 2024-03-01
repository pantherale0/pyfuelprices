"""JET UK module."""

from pyfuelprices.sources.uk import CMAParser, FuelLocation

class JetUKSource(CMAParser):
    """JET uses the CMA parser."""

    _url = "https://jetlocal.co.uk/fuel_prices_data.json"
    provider_name = "jet"
    _timeout = 10
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
