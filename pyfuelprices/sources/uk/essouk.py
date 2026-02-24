"""Esso UK module."""

from pyfuelprices.sources import Source
from pyfuelprices.sources.uk import CMAParserMixIn, FuelLocation

class EssoUKSource(CMAParserMixIn, Source):
    """Esso UK uses the same parser as CMA."""

    country_code = "GB"

    _url = "https://fuelprices.esso.co.uk/latestdata.json"
    provider_name = "essouk"
    _timeout = 60
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
