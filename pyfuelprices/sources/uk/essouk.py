"""Esso UK module."""

from pyfuelprices.sources.uk import CMAParser, FuelLocation

class EssoUKSource(CMAParser):
    """Esso UK uses the same parser as CMA."""

    _url = "https://fuelprices.esso.co.uk/latestdata.json"
    provider_name = "essouk"
    _timeout = 60
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
