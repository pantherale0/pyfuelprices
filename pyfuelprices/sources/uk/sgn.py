"""SGN Retail UK dataprovider."""

from pyfuelprices.fuel import Fuel
from pyfuelprices.sources.uk import CMAParser

class SgnRetailUKSource(CMAParser):
    """SGN Retail UK uses the CMA parser."""

    _url = "https://www.sgnretail.uk/files/data/SGN_daily_fuel_prices.json"
    provider_name = "sgnretail"

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
