"""Ascona Group UK dataprovider."""

from .asda import AsdaUKSource

class AsconaGroupUKSource(AsdaUKSource):
    """Asconagrounp UK uses the same parses as Asda."""

    _url = "https://fuelprices.asconagroup.co.uk/newfuel.json"
    provider_name = "asconagroup"
