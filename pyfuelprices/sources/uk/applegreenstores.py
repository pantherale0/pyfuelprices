"""Applegreen Stores dataprovider."""

from pyfuelprices.sources.uk import CMAParser

class ApplegreenUKSource(CMAParser):
    """Applegreen UK uses the CMA parser."""

    _url = "https://applegreenstores.com/fuel-prices/data.json"
    provider_name = "Applegreen"
