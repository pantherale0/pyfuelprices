"""Rontec UK dataprovider."""

from .asda import AsdaUKSource

class RontecUKSource(AsdaUKSource):
    """Rontec UK uses the same parses as Asda."""

    _url = "https://www.rontec-servicestations.co.uk/fuel-prices/data/fuel_prices_data.json"
    provider_name = "rontec"
