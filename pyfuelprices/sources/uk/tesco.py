"""Tesco UK dataprovider."""

from pyfuelprices.const import DESKTOP_USER_AGENT
from pyfuelprices.fuel import Fuel
from pyfuelprices.sources.uk import CMAParser, FuelLocation

class TescoUKSource(CMAParser):
    """Tesco UK uses the CMA parser."""

    _url = "https://www.tesco.com/fuel_prices/fuel_prices_data.json"
    provider_name = "tesco"
    _headers = {
        "User-Agent": DESKTOP_USER_AGENT,
        "Accept": "application/json",
        "Accept-Language": "en-GB,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1"
    }
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None


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
