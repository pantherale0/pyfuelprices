"""SGN Retail UK dataprovider."""

from pyfuelprices.sources.uk import CMAParser

class SgnRetailUKSource(CMAParser):
    """SGN Retail UK uses the CMA parser."""

    _url = "https://www.sgnretail.uk/files/data/SGN_daily_fuel_prices.json"
    provider_name = "sgnretail"
