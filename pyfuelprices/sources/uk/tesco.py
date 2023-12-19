"""Tesco UK dataprovider."""

from pyfuelprices.sources.uk import CMAParser

class TescoUKSource(CMAParser):
    """Tesco UK uses the CMA parser."""

    _url = "https://www.tesco.com/fuel_prices/fuel_prices_data.json"
    provider_name = "tesco"
