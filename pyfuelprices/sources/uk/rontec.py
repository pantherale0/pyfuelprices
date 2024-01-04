"""Rontec UK dataprovider."""

from pyfuelprices.sources.uk import CMAParser, FuelLocation

class RontecUKSource(CMAParser):
    """Rontec UK uses the same parses as CMA."""

    _url = "https://www.rontec-servicestations.co.uk/fuel-prices/data/fuel_prices_data.json"
    provider_name = "rontec"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
