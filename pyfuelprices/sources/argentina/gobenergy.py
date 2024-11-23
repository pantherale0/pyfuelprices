"""GOB Energy Source."""

import logging
import json
from datetime import datetime, timedelta

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID,
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS
)
from pyfuelprices.sources import Source, geocode_reverse_lookup, geopyexc
from pyfuelprices.fuel import Fuel
from pyfuelprices.fuel_locations import FuelLocation

from .const import AR_GOB_ENERGY_ID, AR_GOB_DATASOURCE, AR_GOB_TIMEOUT

_LOGGER = logging.getLogger(__name__)

class GobEnergySource(Source):
    """GobEnergy fuel source."""

    update_interval = timedelta(hours=12) # hardcoded due to slow servers
    provider_name=AR_GOB_ENERGY_ID
    location_cache: dict[str, FuelLocation] = {}
    _url: str = AR_GOB_DATASOURCE

    async def _send_request(self, url, body) -> str:
        """Send a request to the API and return the raw response."""
        _LOGGER.debug("Sending HTTP request to %s with URL %s", self.provider_name, url)
        async with self._client_session.post(url=AR_GOB_DATASOURCE,
                                            timeout=AR_GOB_TIMEOUT,
                                            json=body) as response:
            if response.ok:
                return await response.text()
            _LOGGER.error("Error sending request to %s: %s",
                            url,
                            response)

    async def search_sites(self, coordinates, radius: float) -> list[dict]:
        """Return all available sites within a given radius."""
        # first query the API to populate cache / update data in case this data is unavailable.
        data = await super().search_sites(coordinates, radius)
        if len(data)>0:
            return data
        await self.update(
            areas=[{
                PROP_AREA_LAT: coordinates[0],
                PROP_AREA_LONG: coordinates[1],
                PROP_AREA_RADIUS: radius
            }],
            force=True
        )
        return await super().search_sites(coordinates, radius)

    async def update(self, areas=None, force=False) -> list[FuelLocation]:
        """Update hooks for the data source."""
        _LOGGER.debug("Starting update hook for %s to url %s", self.provider_name, self._url)
        self._configured_areas=[] if areas is None else areas
        self._clear_cache()
        if self.next_update <= datetime.now() or force:
            for area in self._configured_areas:
                try:
                    geocode = await geocode_reverse_lookup(
                        (area[PROP_AREA_LAT], area[PROP_AREA_LONG])
                    )
                except geopyexc.GeocoderTimedOut:
                    _LOGGER.warning("Timeout occured while geocoding area %s.",
                                    area)
                    continue
                if geocode.raw["address"]["country_code"] != "ar":
                    _LOGGER.debug("Skipping area %s as not in AR.",
                                area)
                    continue
                response = json.loads(await self._send_request(
                    url=self._url,
                    body={
                        "resource_id": "80ac25de-a44a-4445-9215-090cf55cfda5",
                        "q": "",
                        "filters": {
                            "provincia": str(geocode.raw["address"]["state"]).upper(),
                            "localidad": str(geocode.raw["address"]["town"]).upper()
                        },
                        "limit": 500,
                        "offset": 0
                    }
                ))
                if response["success"]:
                    await self.parse_response(response["result"]["records"])
                else:
                    _LOGGER.error("Error sending request to %s: %s",
                                self.provider_name,
                                response)
            self.next_update = datetime.now() + self.update_interval
        return list(self.location_cache.values())

    async def parse_response(self, response) -> list[FuelLocation]:
        """Converts CMA data into fuel price mapping."""
        for location_raw in response:
            site_id = f"{self.provider_name}_{location_raw['idempresa']}"
            location = FuelLocation.create(
                    site_id=site_id,
                    name=f"{location_raw['empresabandera']} {location_raw['empresa']}",
                    address=location_raw["direccion"],
                    brand=location_raw["empresabandera"],
                    lat=location_raw["latitud"],
                    long=location_raw["longitud"],
                    available_fuels=self.parse_fuels(location_raw),
                    postal_code=None,
                    currency="ARS",
                    props={
                        PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                        PROP_FUEL_LOCATION_SOURCE_ID: location_raw["idempresa"],
                        PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True
                    },
                    next_update=self.next_update
                )
            if site_id not in self.location_cache:
                self.location_cache[site_id] = location
            else:
                await self.location_cache[site_id].update(location)
        return list(self.location_cache.values())

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Parses fuel data."""
        return [
            Fuel(
                fuel_type=fuels["producto"],
                props={
                    "fuel_id": fuels["idproducto"],
                    "valid_from": fuels["fecha_vigencia"]
                },
                cost=fuels["precio"]
            )
        ]
