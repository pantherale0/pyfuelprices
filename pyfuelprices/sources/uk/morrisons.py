"""Morrisons UK dataprovider."""

from pyfuelprices.sources.uk import CMAParser

class MorrisonsUKSource(CMAParser):
    """Morrisons UK uses the CMA parser."""

    _url = "https://www.morrisons.com/fuel-prices/fuel.json"
    provider_name = "morrisons"
    _headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
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
