"""BP UK dataprovider."""

from pyfuelprices.const import DESKTOP_USER_AGENT
from pyfuelprices.fuel import Fuel
from pyfuelprices.sources.uk import CMAParser, FuelLocation

class BpUKSource(CMAParser):
    """BP UK uses the CMA parser."""

    _url = "https://www.bp.com/en_gb/united-kingdom/home/fuelprices/fuel_prices_data.json"
    provider_name = "bpuk"
    _headers = {
        "User-Agent": DESKTOP_USER_AGENT
    }
    _timeout = 60
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Parses fuel data."""
        f_list = []
        for f_type in fuels:
            f_list.append(Fuel(
                fuel_type=f_type,
                cost=round(fuels[f_type]*100, 1),
                props={}
            ))
        return f_list
