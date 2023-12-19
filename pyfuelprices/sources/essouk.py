"""Esso UK module."""

from pyfuelprices.sources.asda import AsdaUKSource

class EssoUKSource(AsdaUKSource):
    """The main source."""

    _url = "https://fuelprices.esso.co.uk/latestdata.json"
    provider_name = "essouk"
    _timeout = 60
