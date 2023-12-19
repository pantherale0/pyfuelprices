"""Sainsburys UK dataprovider."""

from .asda import AsdaUKSource

class SainsburysUKSource(AsdaUKSource):
    """Sainsburys UK uses the same parses as Asda."""

    _url = "https://api.sainsburys.co.uk/v1/exports/latest/fuel_prices_data.json"
    provider_name = "sainsburys"
