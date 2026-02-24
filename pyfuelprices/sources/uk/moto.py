"""Motor Fuel Group UK dataprovider."""

from pyfuelprices.sources import Source
from pyfuelprices.sources.uk import CMAParser, FuelLocation

class MotowayUKSource(CMAParser, Source):
    """Moto-Way UK uses the CMA parser."""

    _url = "https://moto-way.com/fuel-price/fuel_prices.json"
    provider_name = "motoway"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
