"""Asda UK module."""

from pyfuelprices.sources.uk import CMAParser, FuelLocation

class AsdaUKSource(CMAParser):
    """Asda uses the CMA parser."""

    _url = "https://storelocator.asda.com/fuel_prices_data.json"
    provider_name = "asda"
    _timeout = 10
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
