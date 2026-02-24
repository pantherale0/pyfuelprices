"""Asda UK module."""

from pyfuelprices.sources import Source
from pyfuelprices.sources.uk import CMAParserMixIn, FuelLocation

class AsdaUKSource(CMAParserMixIn, Source):
    """Asda uses the CMA parser."""

    country_code = "GB"

    _url = "https://storelocator.asda.com/fuel_prices_data.json"
    provider_name = "asda"
    _timeout = 10
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
