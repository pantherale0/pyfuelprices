"""SGN Retail UK dataprovider."""

from .asda import AsdaUKSource

class SgnRetailUKSource(AsdaUKSource):
    """SGN Retail UK uses the same parses as Asda."""

    _url = "https://www.sgnretail.uk/files/data/SGN_daily_fuel_prices.json"
    provider_name = "sgnretail"
