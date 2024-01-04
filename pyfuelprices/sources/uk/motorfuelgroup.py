"""Motor Fuel Group UK dataprovider."""

from pyfuelprices.sources.uk import CMAParser, FuelLocation

class MotorFuelGroupUKSource(CMAParser):
    """Motor Fuel Group UK uses the CMA parser."""

    _url = "https://fuel.motorfuelgroup.com/fuel_prices_data.json"
    provider_name = "motorfuelgroup"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
