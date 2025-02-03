"""Data source for PetrolPrices UK."""

import asyncio
import logging

from datetime import datetime, timedelta

from pyfuelprices.const import (
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID
)

from pyfuelprices.sources import Source, FuelLocation, Fuel

from .const import (
    CONST_PETROLPRICES_BASE,
    CONST_PETROLPRICES_FUELSTATIONS,
    CONST_PETROLPRICES_LOGIN,
    CONST_PETROLPRICES_FUEL_MAP
)

_LOGGER = logging.getLogger(__name__)

class PetrolPricesUKSource(Source):
    """PetrolPrices source."""

    _headers = {
        "Accept": "application/json",
        "User-Agent": "okhttp/4.9.2"
    }
    _access_token: str = ""
    _refresh_token: str = ""
    _at_expires: datetime | None = None
    _at_update_lock: asyncio.Lock = asyncio.Lock()
    _fs_update_lock: asyncio.Lock = asyncio.Lock()
    provider_name = "petrolprices"
    location_cache = {}

    async def search_sites(self, coordinates, radius: float) -> list[dict]:
        """Return all available sites within a given radius."""
        # first query the API to populate cache / update data in case this data is unavailable.
        data = await super().search_sites(coordinates, radius)
        if len(data)>0:
            return data
        await self.update(
            areas=[
                {
                    PROP_AREA_LAT: coordinates[0],
                    PROP_AREA_LONG: coordinates[1],
                    PROP_AREA_RADIUS: radius
                }
            ],
            force=True
        )
        return await super().search_sites(coordinates, radius)

    async def _send_request(self, url, method) -> None | dict:
        """Send a HTTP request."""
        _LOGGER.debug("Sending %s request to %s", method, url)
        if "guest-mode/gello" not in url:
            await self._refresh_access_token()
        else:
            self._access_token = ""
            self._refresh_token = ""
        async with self._client_session.request(
            method=method,
            url=url,
            timeout=30,
            headers={
                **self._headers,
                "authorization": self._access_token,
                "refresh-token": self._refresh_token
            }
        ) as resp:
            _LOGGER.debug("Got status code %s for request %s",
                          resp.status, url)
            if resp.status != 200:
                _LOGGER.error("Request to %s failed %s (%s)",
                              url,
                              resp.status,
                              await resp.text())
                return
            return await resp.json()

    async def _refresh_access_token(self):
        """Refresh the access token if needed."""
        async with self._at_update_lock:
            if self._at_expires is None or self._at_expires < datetime.now():
                _LOGGER.debug("Refreshing access token.")
                response = await self._send_request(
                    CONST_PETROLPRICES_LOGIN.format(BASE=CONST_PETROLPRICES_BASE),
                    "POST"
                )
                if response is None:
                    pass
                self._access_token = response["accessToken"]
                self._refresh_token = response["refreshToken"]
                self._at_expires = datetime.now() + timedelta(hours=23)

    async def update_area(self, area: dict, fuel_type: str, fuel_code: str):
        """Update a given area."""
        response = await self._send_request(
            CONST_PETROLPRICES_FUELSTATIONS.format(
                BASE=CONST_PETROLPRICES_BASE,
                FUEL_TYPE=fuel_type,
                RADIUS=area[PROP_AREA_RADIUS],
                LAT=area[PROP_AREA_LAT],
                LNG=area[PROP_AREA_LONG]
            ),
            method="GET"
        )
        if response is None:
            return
        response["fuel_code"] = fuel_code
        await self.parse_response(response)

    async def update(self, areas=None, force=False):
        """Update PetrolPrices data."""
        self._configured_areas = areas or []
        self._clear_cache()
        if self.next_update > datetime.now() and not force:
            return
        coros = [
            self.update_area(a, ft, code) for a in self._configured_areas
            for ft, code in CONST_PETROLPRICES_FUEL_MAP.items()
        ]
        results = await asyncio.gather(*coros)
        for result in results:
            if isinstance(result, Exception):
                _LOGGER.exception("Error updating area: %s", result)
        return list(self.location_cache.values())

    async def parse_or_update_station(self, station: dict, fuel_type: str):
        """Parse or update the fuel station."""
        _LOGGER.debug("Parsing station %s", station["idstation"])
        site_id = f"{self.provider_name}_{station['idstation']}"
        price = float(station["price"]) / 1000
        fuel = Fuel(
            fuel_type=fuel_type,
            cost=price if price > 0 else -1,
            props={
                **station["fuel"],
                "available": price>0}
        )
        loc = FuelLocation.create(
            site_id=site_id,
            name=station["name"],
            address="See properties",
            lat=station["lat"],
            long=station["lng"],
            brand=station["fuel_brand_name"],
            available_fuels=[] if fuel.cost == -1 else [fuel],
            postal_code=station["postcode"],
            currency="GBP",
            props={
                "data": station,
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: station['idstation']
            },
            next_update=self.next_update+self.update_interval
        )
        async with self._fs_update_lock:
            if site_id not in self.location_cache:
                self.location_cache[site_id] = loc
            else:
                await self.location_cache[site_id].update(loc)
        return self.location_cache[site_id]

    async def parse_response(self, response: dict) -> list[FuelLocation]:
        """Parse a fuel response."""
        if "error" in response and response["error"]:
            _LOGGER.error("PetrolPrices API Returned an unknown error.")
            return
        if "data" not in response and not isinstance(response["data"], list):
            return
        for station in response["data"]:
            await self.parse_or_update_station(station, response["fuel_code"])
        return self.location_cache

    def parse_fuels(self, fuels):
        """Not used."""
