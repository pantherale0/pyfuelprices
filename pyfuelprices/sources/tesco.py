"""Tesco UK dataprovider."""

from .asda import AsdaUKSource

class TescoUKSource(AsdaUKSource):
    """Tesco UK uses the same parses as Asda."""

    _url = "https://www.tesco.com/fuel_prices/fuel_prices_data.json"
    provider_name = "tesco"
