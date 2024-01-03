"""Data source for PetrolPrices."""

import logging
import asyncio
from datetime import datetime, timedelta

import aiohttp

from pyfuelprices.fuel_locations import Fuel, FuelLocation
from pyfuelprices.sources import Source
from pyfuelprices.const import (
    CONF_PRELOAD_AREA_LAT,
    CONF_PRELOAD_AREA_LONG,
    CONF_PRELOAD_AREA_RADIUS,
    CONF_FUEL_LOCATION_DYNAMIC_BUILD
)

_LOGGER = logging.getLogger(__name__)

FUELPRICES_API_BASE = "https://mobile.app.petrolprices.com/api"
FUELPRICES_API_AUTH = f"{FUELPRICES_API_BASE}/guest-mode/gello"
FUELPRICES_API_GEOLOOKUP = (
    FUELPRICES_API_BASE +
    "/petrolstationsgeo/{FUEL_TYPE}/0/50/0/{RADIUS}/price?lat={LAT}&lng={LNG}"
)
FUELPRICES_API_STATION = FUELPRICES_API_BASE + "/petrolstation/{STN_ID}"


class PetrolPricesFuelLocation(FuelLocation):
    """PetrolPrices fuel location."""

    next_update: datetime = datetime.now()
    update_interval = timedelta(days=1) # prevents over loading the API.

    def _build_fuel(self, response: dict, f_type: str):
        """Build fuel type."""
        if response.get("price", None) is None:
            response["price"] = 0
        return Fuel(
            fuel_type=f_type,
            cost=response.get("price", 0) / 10,
            props=response
        )

    async def dynamic_build_fuels(self):
        """Retrieve data from the source."""
        if (len(self.available_fuels) != 0 and self.next_update > datetime.now()):
            return None
        async with aiohttp.ClientSession(
            headers=self.props["headers"]
        ) as session:
            async with session.request(
                method="GET",
                url=FUELPRICES_API_STATION.format(
                    STN_ID=str(self.id)
                )
            ) as response:
                if response.status == 200:
                    _LOGGER.debug("Dynamic build for station %s got response %s",
                                  self.id,
                                  response.status)
                    response_json = await response.json()
                    response_json = response_json.get("data", [{}])[0]
                    self.available_fuels.append(self._build_fuel(
                        response_json.get("super_unleaded", {}), "E10"
                    ))
                    self.available_fuels.append(self._build_fuel(
                        response_json.get("unleaded", {}), "E5"
                    ))
                    self.available_fuels.append(self._build_fuel(
                        response_json.get("diesel", {}), "B7"
                    ))
                    self.available_fuels.append(self._build_fuel(
                        response_json.get("diesel", {}), "B10"
                    ))
        self.next_update += self.update_interval

class PetrolPricesSource(Source):
    """Main PetrolPrices data source."""

    _headers: dict = {
        "authorization": "",
        "refresh-token": ""
    }
    _locations_temp: dict[str, PetrolPricesFuelLocation] = {}
    provider_name="petrolprices"

    async def authorization(self):
        """Login to PetrolPrices."""
        async with self._client_session.request(
            method="POST",
            url=FUELPRICES_API_AUTH
        ) as response:
            _LOGGER.debug("Authentication response code %s", response.status)
            if response.status == 200:
                js = await response.json()
                self._headers["authorization"] = js["accessToken"]
                self._headers["refresh-token"] = js["refreshToken"]
                _LOGGER.debug("Authorization complete.")
            else:
                raise ConnectionError(response)

    async def send_request(self,
                            lat: str,
                            long: str,
                            radius: float) -> dict:
        """Send a request to PetrolPrices to retrieve data."""
        async with self._client_session.request(
            method="GET",
            url=FUELPRICES_API_GEOLOOKUP.format(
                FUEL_TYPE=2,
                RADIUS=radius,
                LAT=lat,
                LNG=long
            ),
            headers=self._headers
        ) as response:
            _LOGGER.debug("Update request completed for %s with status %s",
                          self.provider_name, response.status)
            if response.status == 200:
                return await response.json()

    async def update(self,
                     preload_areas: dict[str, dict[str, object]] = None
                    ) -> list[PetrolPricesFuelLocation]:
        """Update PetrolPrices data."""
        await self.authorization()
        self._locations_temp = {}
        for area in preload_areas.values():
            response = await self.send_request(
                lat=area[CONF_PRELOAD_AREA_LAT],
                long=area[CONF_PRELOAD_AREA_LONG],
                radius=area[CONF_PRELOAD_AREA_RADIUS]
            )
            self.parse_response(
                response=response
            )
        coros = [s.dynamic_build_fuels()
                 for s in list(self._locations_temp.values())]
        await asyncio.gather(*coros)
        return list(self._locations_temp.values())

    def parse_response(self, response: dict) -> list[PetrolPricesFuelLocation]:
        """Parse a response into fuel locations,"""
        for raw in response.get("data", []):
            if str(raw["idstation"]) not in self._locations_temp:
                _LOGGER.debug("Parsing location %s", raw["idstation"])
                fuel_loc = PetrolPricesFuelLocation.create(
                    site_id=raw["idstation"],
                    name=raw["name"],
                    address=(
                        raw["address1"] + " " +
                        raw["address2"] + " " +
                        raw["town"] + " " +
                        raw["county"]),
                    lat=raw["lat"],
                    long=raw["lng"],
                    brand=raw["fuel_brand_name"],
                    available_fuels=[],
                    postal_code=raw["postcode"]
                )
                fuel_loc.props[CONF_FUEL_LOCATION_DYNAMIC_BUILD] = True
                fuel_loc.props["headers"] = self._headers
                self._locations_temp[raw["idstation"]] = fuel_loc

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Parse Fuels not used for PetrolPrices."""
