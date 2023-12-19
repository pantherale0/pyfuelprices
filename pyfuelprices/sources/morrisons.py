"""Morrisons UK dataprovider."""

from .asda import AsdaUKSource

class MorrisonsUKSource(AsdaUKSource):
    """Morrisons UK uses the same parses as Asda."""

    _url = "https://www.morrisons.com/fuel-prices/fuel.json"
    provider_name = "morrisons"
    _headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1"
    }
