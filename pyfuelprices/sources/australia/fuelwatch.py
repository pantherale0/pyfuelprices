"""FuelWatch data source for Australia."""

from datetime import datetime

import logging
import json

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_SOURCE_ID,
    DESKTOP_USER_AGENT
)
from pyfuelprices.fuel_locations import FuelLocation, Fuel
from pyfuelprices.sources import Source

from .const import FUELWATCH_API_PRODUCTS, FUELWATCH_API_SITES

_LOGGER = logging.getLogger(__name__)

class FuelWatchSource(Source):
    """FuelWatch data source."""
    provider_name = "fuelwatch"
    _fuel_products: list[str] = []
    _headers = {
        "User-Agent": DESKTOP_USER_AGENT
    }
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None

    async def _send_request(self, url):
        """Send a HTTP request to the API and return the text."""
        async with self._client_session.get(
            url,
            headers=self._headers) as response:
            if response.ok:
                return await response.text()
            _LOGGER.error("Error sending request to %s: %s",
                            url,
                            response)

    async def get_fuel_products(self):
        """Retrieves available fuel products."""
        response_raw = await self._send_request(FUELWATCH_API_PRODUCTS)
        for product in json.loads(response_raw):
            if product["shortName"] not in self._fuel_products:
                self._fuel_products.append(product["shortName"])
        return self._fuel_products

    def _parse_raw_fuel_station(self, station, site_id) -> FuelLocation:
        """Convert an instance of a single fuel station into a FuelLocation."""
        _LOGGER.debug("Parsing FuelWatch location ID %s", site_id)
        loc = FuelLocation.create(
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
        loc.next_update = self.next_update + self.update_interval
        return loc

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

    async def update(self, areas=None, force=None) -> list[FuelLocation]:
        """Custom update handler to look all products."""
        # _df_columns = ["lat", "long"]
        # _df_data = []
        if datetime.now() > self.next_update:
            if len(self._fuel_products) == 0:
                await self.get_fuel_products()
            for product in self._fuel_products:
                url = FUELWATCH_API_SITES.format(
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
            # for x in self.location_cache.values():
            #     _df_data.append([x.lat, x.long])
            # _df = pd.DataFrame(_df_data, columns=_df_columns)
            # self.location_tree = KDTree(_df[["lat", "long"]].values,
            #                             metric="euclidean")
            self.next_update += self.update_interval
            return list(self.location_cache.values())

    async def parse_response(self, response) -> list[FuelLocation]:
        """Method not used."""

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Method not used."""
