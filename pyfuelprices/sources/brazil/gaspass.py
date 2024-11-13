"""GasPass data source."""

import logging
import json

from datetime import datetime, timedelta

from pyfuelprices.const import (
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID,
)
from pyfuelprices.fuel_locations import Fuel, FuelLocation
from pyfuelprices.sources import (
    Source,
    geocode_reverse_lookup,
    geopyexc
)

_LOGGER = logging.getLogger(__name__)

CONST_GASPASS_API_BASE = "https://gaspassproxy-cwa7dsbnadhwbhfe.brazilsouth-01.azurewebsites.net/api/v1/gaspass"
CONST_FUELS = [
    "ultimo_preco_alcool",
    "ultimo_preco_diesel",
    "ultimo_preco_diesel_s10",
    "ultimo_preco_gasolina",
    "ultimo_preco_gasolina_adt",
    "ultimo_preco_gnv"
]

class GasPassSource(Source):
    """GasPass Source."""
    provider_name = "gaspass"
    location_cache: dict[str, FuelLocation] = {}
    update_interval = timedelta(hours=6) # limit update interval to prevent overloading proxy

    async def _send_request(self, lat, long, radius):
        """Send a request to the API for a given postcode and radius."""
        radius = radius * 1.609344 # convert miles to km
        _LOGGER.debug("Sending request to gaspass: %s",
                      CONST_GASPASS_API_BASE)
        async with self._client_session.post(
            CONST_GASPASS_API_BASE,
            headers=self._headers,
            json={
                "lat": lat,
                "long": long,
                "radius": radius
            }) as response:
            if response.ok:
                return await response.text()
            _LOGGER.error("Error sending request to %s: %s",
                            CONST_GASPASS_API_BASE,
                            response)

    async def update(self, areas=None, force=None) -> list[FuelLocation]:
        """Custom update handler as this needs to query GasPass on areas."""
        if datetime.now() > self.next_update or force:
            self._configured_areas=[] if areas is None else areas
            for area in self._configured_areas:
                try:
                    geocode = await geocode_reverse_lookup(
                        (area[PROP_AREA_LAT], area[PROP_AREA_LONG])
                    )
                except geopyexc.GeocoderTimedOut:
                    _LOGGER.warning("Timeout occured while geocoding area %s.",
                                    area)
                    continue
                if geocode.raw["address"]["country_code"] != "br":
                    _LOGGER.debug("Skipping area %s as not in BR.",
                                area)
                    continue
                response_raw = json.loads(await self._send_request(
                    lat=area[PROP_AREA_LAT],
                    long=area[PROP_AREA_LONG],
                    radius=area[PROP_AREA_RADIUS]
                ))
                if response_raw["message"] == "ok":
                    await self.parse_response(response_raw["data"])
                else:
                    _LOGGER.error("Error sending request to %s: %s",
                                self.provider_name,
                                response_raw)
            self.next_update += self.update_interval
        return list(self.location_cache.values())

    def _parse_raw(self, station: dict) -> FuelLocation:
        """Parse a single raw instance of a fuel site."""
        site_id = f"{self.provider_name}_{station['id']}"
        _LOGGER.debug("Parsing GasPass location ID %s", site_id)
        loc = FuelLocation.create(
            site_id=site_id,
            name=station["Auto Posto Bixiga"],
            address=station['endereco'],
            lat=station["geocode"]["latitude"],
            long=station["geocode"]["longitude"],
            brand=station["bandeira"]["nome"],
            available_fuels=self.parse_fuels(station),
            postal_code=None,
            currency="BRL",
            props={
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: station["id"],
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
            }
        )
        loc.next_update = self.next_update if self.next_update > datetime.now() else (
            self.next_update + self.update_interval
        )
        return loc

    async def parse_response(self, response) -> list[FuelLocation]:
        for station_raw in response.get("response", []):
            station = self._parse_raw(station_raw)
            if station.id not in self.location_cache:
                self.location_cache[station.id] = station
            else:
                await self.location_cache[station.id].update(station)
        return list(self.location_cache.values())

    def parse_fuels(self, fuels: dict[str, object]) -> list[Fuel]:
        """Parse fuel data from GasPass."""
        fuels_parsed = []
        for k in CONST_FUELS:
            if k in fuels and fuels[k] is not None:
                fuels_parsed.append(Fuel(
                    fuel_type=k.replace("ultimo_preco_", "").upper(),
                    cost=fuels[k],
                    props={}
                ))
        return fuels_parsed
