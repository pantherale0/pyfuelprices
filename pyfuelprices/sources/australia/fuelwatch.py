"""FuelWatch data source for Australia."""

from datetime import datetime

import logging
import json

import aiohttp

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_SOURCE_ID
)
from pyfuelprices.fuel_locations import FuelLocation, Fuel
from pyfuelprices.sources import Source

_LOGGER = logging.getLogger(__name__)

CONST_FUELWATCH_API_BASE = "https://www.fuelwatch.wa.gov.au/api/"
CONST_FUELWATCH_API_PRODUCTS = f"{CONST_FUELWATCH_API_BASE}products"
CONST_FUELWATCH_API_SITES = (
    f"{CONST_FUELWATCH_API_BASE}sites"
    "?fuelType={FUELTYPE}"
)

class FuelWatchSource(Source):
    """FuelWatch data source."""
    provider_name = "fuelwatch"
    _fuel_products: list[str] = []
    _headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
    }
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None

    async def _send_request(self, url):
        """Send a HTTP request to the API and return the text."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.ok:
                    return await response.text()
                _LOGGER.error("Error sending request to %s: %s",
                              url,
                              response)

    async def get_fuel_products(self):
        """Retrieves available fuel products."""
        response_raw = await self._send_request(CONST_FUELWATCH_API_PRODUCTS)
        for product in json.loads(response_raw):
            if product["shortName"] not in self._fuel_products:
                self._fuel_products.append(product["shortName"])
        return self._fuel_products

    def _parse_raw_fuel_station(self, station, site_id) -> FuelLocation:
        """Convert an instance of a single fuel station into a FuelLocation."""
        _LOGGER.debug("Parsing FuelWatch location ID %s", site_id)
        return FuelLocation.create(
            site_id=site_id,
            name=station["siteName"],
            address=f"{station['address']['line1']} {station['address']['postCode']}",
            lat=station['address']['latitude'],
            long=station['address']['longitude'],
            brand=station['brandName'],
            available_fuels=[Fuel(
                fuel_type=station["productFuelType"],
                cost=station["product"].get("priceToday", 0),
                props=station["product"]
            )],
            postal_code=station['address']['postCode'],
            currency="",
            props={
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: station["id"],
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                "data": station
            }
        )

    def _update_fuel_station_prices(self, station, site_id):
        """Internal method to update station prices."""
        try:
            self.location_cache[site_id].get_fuel(station["productFuelType"]).update(
                fuel_type=station["productFuelType"],
                cost=station["product"].get("priceToday", 0),
                props=station["product"]
            )
        except ValueError:
            self.location_cache[site_id].available_fuels.append(
                Fuel(
                    fuel_type=station["productFuelType"],
                    cost=station["product"].get("priceToday", 0),
                    props=station["product"]
                )
            )

    async def update(self, areas=None) -> list[FuelLocation]:
        """Custom update handler to look all products."""
        if datetime.now() > self.next_update:
            if len(self._fuel_products) == 0:
                await self.get_fuel_products()
            for product in self._fuel_products:
                url = CONST_FUELWATCH_API_SITES.format(
                    FUELTYPE=product
                )
                response_raw = json.loads(await self._send_request(url))
                for station in response_raw:
                    site_id = f"{self.provider_name}_{station['id']}"
                    if site_id in self.location_cache:
                        self._update_fuel_station_prices(station, site_id)
                        continue
                    loc = self._parse_raw_fuel_station(station, site_id)
                    self.location_cache[loc.id] = loc
                    continue
            return list(self.location_cache.values())

    async def parse_response(self, response) -> list[FuelLocation]:
        """Method not used."""

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Method not used."""