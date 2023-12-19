"""BP UK dataprovider."""

from .asda import AsdaUKSource

class BpUKSource(AsdaUKSource):
    """BP UK uses the same parses as Asda."""

    _url = "https://www.bp.com/en_gb/united-kingdom/home/fuelprices/fuel_prices_data.json"
    provider_name = "bpuk"
    _headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
    }
    _timeout = 60
