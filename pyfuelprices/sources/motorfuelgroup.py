"""Motor Fuel Group UK dataprovider."""

from .asda import AsdaUKSource

class MotorFuelGroupUKSource(AsdaUKSource):
    """Motor Fuel Group UK uses the same parses as Asda."""

    _url = "https://fuel.motorfuelgroup.com/fuel_prices_data.json"
    provider_name = "motorfuelgroup"
