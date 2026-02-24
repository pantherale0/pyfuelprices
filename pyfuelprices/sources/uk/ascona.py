"""Ascona Group UK dataprovider."""

from pyfuelprices.sources import Source
from pyfuelprices.sources.uk import CMAParserMixIn, FuelLocation

class AsconaGroupUKSource(CMAParserMixIn, Source):
    """Asconagrounp UK uses the CMA parser."""

    country_code = "GB"

    _url = "https://fuelprices.asconagroup.co.uk/newfuel.json"
    provider_name = "ascona"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
