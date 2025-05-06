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
from pyfuelprices.helpers import geocoder, geopyexc
from pyfuelprices.sources import (
    Source,
    UpdateFailedError
)
from .const import (
    CONST_FUELS,
    CONST_GET_FUELS
)

_LOGGER = logging.getLogger(__name__)

class GasPassSource(Source):
    """GasPass Source."""
    provider_name = "gaspass"
    location_cache: dict[str, FuelLocation] = {}

    def __init__(self, configured_areas = None, update_interval = ..., client_session = None, configuration = None):
        if update_interval.seconds < 3600:
            update_interval = timedelta(hours=1)
        super().__init__(configured_areas, update_interval, client_session, configuration)

    async def _send_request(self, lat, long, radius):
        """Send a request to the API for a given postcode and radius."""
        radius = radius * 1.609344 # convert miles to km
        _LOGGER.debug("Sending request to gaspass: %s",
                      CONST_GET_FUELS)
        async with self._client_session.request(
            method="POST",
            url=CONST_GET_FUELS,
            json={
                "lat": lat,
                "long": long,
                "radius": radius
            },
            headers={"Content-Type": "application/json"}) as response:
            if not response.ok:
                text = await response.text()
                _LOGGER.error("Error sending request to %s: %s",
                                CONST_GET_FUELS,
                                text)
                raise UpdateFailedError(
                    response.status,
                    response=text,
                    headers=response.headers,
                    service=self.provider_name
                )
            return await response.text()

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

    async def update_area(self, area) -> bool:
        """Update a given area."""
        try:
            geocode = await geocoder.geocode_reverse_lookup(
                (area[PROP_AREA_LAT], area[PROP_AREA_LONG])
            )
        except geopyexc.GeocoderTimedOut:
            _LOGGER.warning("Timeout occured while geocoding area %s.",
                            area)
            return False
        if geocode.raw["address"]["country_code"] != "br":
            _LOGGER.debug("Skipping area %s as not in BR.",
                        area)
            return False
        response_raw = json.loads(await self._send_request(
            lat=area[PROP_AREA_LAT],
            long=area[PROP_AREA_LONG],
            radius=area[PROP_AREA_RADIUS]
        ))
        if response_raw["message"] == "ok":
            await self.parse_response(response_raw)
            return True
        _LOGGER.error("Error sending request to %s: %s",
                    self.provider_name,
                    response_raw)
        return False

    def _parse_raw(self, station: dict) -> FuelLocation:
        """Parse a single raw instance of a fuel site."""
        site_id = f"{self.provider_name}_{station['id']}"
        _LOGGER.debug("Parsing GasPass location ID %s", site_id)
        loc = FuelLocation.create(
            site_id=site_id,
            name=station["nome_fantasia"],
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
