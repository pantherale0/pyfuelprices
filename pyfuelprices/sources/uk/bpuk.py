"""BP UK dataprovider."""

from pyfuelprices.fuel import Fuel
from pyfuelprices.sources.uk import CMAParser

class BpUKSource(CMAParser):
    """BP UK uses the CMA parser."""

    _url = "https://www.bp.com/en_gb/united-kingdom/home/fuelprices/fuel_prices_data.json"
    provider_name = "bpuk"
    _headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
    }
    _timeout = 60

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Parses fuel data."""
        f_list = []
        for f_type in fuels:
            f_list.append(Fuel(
                fuel_type=f_type,
                cost=fuels[f_type]*100,
                props={}
            ))
        return f_list
