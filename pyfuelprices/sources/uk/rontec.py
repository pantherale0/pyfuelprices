"""Rontec UK dataprovider."""

from pyfuelprices.sources import Source
from pyfuelprices.sources.uk import CMAParserMixIn, FuelLocation

class RontecUKSource(CMAParserMixIn, Source):
    """Rontec UK uses the same parses as CMA."""

    country_code = "GB"

    _url = "https://www.rontec-servicestations.co.uk/fuel-prices/data/fuel_prices_data.json"
    provider_name = "rontec"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
