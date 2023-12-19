"""Applegreen Stores dataprovider."""

from .asda import AsdaUKSource

class ApplegreenUKSource(AsdaUKSource):
    """Applegreen UK uses the same parses as Asda."""

    _url = "https://applegreenstores.com/fuel-prices/data.json"
    provider_name = "Applegreen"
