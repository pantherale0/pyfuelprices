"""PodPoint data source."""

import asyncio
import logging

from datetime import datetime

from pyfuelprices.const import (
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID
)
from pyfuelprices.sources import Source, geocode_reverse_lookup, geopyexc
from pyfuelprices.fuel_locations import Fuel, FuelLocation

from .const import CONST_PODPOINT_BASE, CONST_PODPOINT_LOCATION, CONST_PODPOINT_SEARCH

_LOGGER = logging.getLogger(__name__)

class PodPointSource(Source):
    """Pod Point data source."""
    provider_name="podpoint"
    _headers = {
        "User-Agent": "POD Point Native Mobile App/3.27.12 (Android/14)"
    }
    location_cache: dict[str, FuelLocation] = {}

    async def _send_request(self, url) -> dict:
        """Send a request to the API and return the raw response."""
        _LOGGER.debug("Sending HTTP request to FuelGR with URL %s", url)
        async with self._client_session.get(url=url,
                                            headers=self._headers) as response:
            if response.ok:
                return await response.json()
            _LOGGER.error("Error sending request to %s: %s",
                            url,
                            response)

    async def search_sites(self, coordinates, radius: float) -> list[dict]:
        """Return all available sites (radius not used)"""
        # first query the API to populate the cache / update data
        data = await super().search_sites(coordinates, radius)
        if len(data)>0:
            return data
        await self.update_area(
            {
                PROP_AREA_LAT: coordinates[0],
                PROP_AREA_LONG: coordinates[1]
            }
        )
        return await super().search_sites(coordinates, radius)

    async def update_area(self, area: dict):
        """Update a single area."""
        try:
            geocode = await geocode_reverse_lookup(
                (area[PROP_AREA_LAT], area[PROP_AREA_LONG])
            )
        except geopyexc.GeocoderTimedOut:
            _LOGGER.warning("Timeout occured while geocoding area %s.",
                            area)
            return None
        if geocode.raw["address"]["country_code"] != "gb":
            _LOGGER.debug("Skipping area %s as not in GB.",
                        area)
            return None
        _LOGGER.debug("Searching Pod Point for FuelLocations at area %s", area)
        response_raw = await self._send_request(
            url=CONST_PODPOINT_SEARCH.format(
                BASE=CONST_PODPOINT_BASE,
                LAT=area[PROP_AREA_LAT],
                LNG=area[PROP_AREA_LONG]
            )
        )
        await self.parse_response(response_raw)

    async def get_and_parse_pod(self, response: dict):
        """Retrieves pod details and parses the response."""
        _LOGGER.debug("Parsing object %s", response["id"])
        site_id = f"{self.provider_name}_{response['id']}"
        fs = FuelLocation.create(
            site_id=site_id,
            name=response["name"],
            address="See properties",
            lat=response["location"]["lat"],
            long=response["location"]["lng"],
            brand="Pod Point",
            available_fuels=[],
            currency="GBP",
            postal_code=response["address"]["postcode"],
            next_update=self.next_update,
            props={
                **response,
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: response["id"],
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True
            }
        )
        pods = self.parse_fuels(await self._send_request(
            url=CONST_PODPOINT_LOCATION.format(
                BASE=CONST_PODPOINT_BASE,
                LOC_ID=response["id"]
            )
        ))
        for pod in pods:
            fs.add_or_update_fuel(pod)
            fs.next_update=self.next_update
            fs.last_updated=datetime.now()
        if site_id not in self.location_cache:
            self.location_cache[site_id] = fs
        else:
            self.location_cache.get(site_id).update(fs)
        _LOGGER.debug("Parsed object %s", response["id"])

    def parse_fuels(self, fuels: list[dict]):
        """Parse fuels."""
        # EV will use the fuel type format "EV-POWER kW"
        fuels_parsed = []
        fuels = fuels["pods"]
        for f in fuels:
            if "unit_connectors" not in f:
                continue
            if not isinstance(f["unit_connectors"], list):
                continue
            if len(f["unit_connectors"]) == 0:
                continue
            if "price" not in f:
                continue
            if not isinstance(f["price"], dict):
                continue
            if "cost" not in f["price"]:
                continue
            if not isinstance(f["price"]["cost"], list):
                continue
            if len(f["price"]["cost"]) == 0:
                continue
            connector = f["unit_connectors"][0]['connector']
            fuels_parsed.append(Fuel(
                fuel_type=f"EV-{connector['power']} kW",
                cost=f["price"]["cost"][0]["price"]/100,
                props=f
            ))
        return fuels_parsed

    async def parse_response(self, response):
        """Parse fuel station response."""
        coros = [self.get_and_parse_pod(x) for x in response["addresses"]]
        await asyncio.gather(*coros)

    async def update(self, areas=None, force=False):
        """Update data source."""
        if self.next_update <= datetime.now() or force:
            self._configured_areas=[] if areas is None else areas
            try:
                self.next_update += self.update_interval
                coros = [self.update_area(a) for a in self._configured_areas]
                await asyncio.gather(*coros)
            except Exception as exc:
                _LOGGER.exception(exc, exc_info=exc)

        return list(self.location_cache.values())
