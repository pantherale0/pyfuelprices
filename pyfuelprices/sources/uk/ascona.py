"""Ascona Group UK dataprovider."""

from pyfuelprices.sources.uk import CMAParser, FuelLocation

class AsconaGroupUKSource(CMAParser):
    """Asconagrounp UK uses the CMA parser."""

    _url = "https://fuelprices.asconagroup.co.uk/newfuel.json"
    provider_name = "ascona"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
