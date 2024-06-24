"""FuelGR Service for Greece."""

import logging
import asyncio

from datetime import timedelta, datetime

import xmltodict
from geopy import distance

from pyfuelprices.const import (
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID
)
from pyfuelprices.sources import Source, geocode_reverse_lookup, geopyexc
from pyfuelprices.fuel_locations import Fuel, FuelLocation

from .const import (
    FUELGR_GET_DATA,
    FUELGR_GET_STATION_PRICES,
    FUELGR_FUEL_TYPE_MAPPING
)

_LOGGER = logging.getLogger(__name__)

class FuelGrSource(Source):
    """The root FuelGR data source."""

    update_interval = timedelta(days=1) # update once per day to prevent API spam.
    provider_name = "fuelgr"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
    _parser_coords = None

    async def _send_request(self, url) -> str:
        """Send a request to the API and return the raw response."""
        _LOGGER.debug("Sending HTTP request to FuelGR with URL %s", url)
        async with self._client_session.get(url=url,
                                            headers=self._headers) as response:
            if response.ok:
                return await response.text()
            _LOGGER.error("Error sending request to %s: %s",
                            url,
                            response)

    async def get_site(self, site_id) -> FuelLocation:
        """Return a single site."""
        return self.location_cache[site_id]

    async def search_sites(self, coordinates, radius: float) -> list[dict]:
        """Return all available sites (radius not used)"""
        # first query the API to populate the cache / update data
        await self.update_area(
            {
                PROP_AREA_LAT: coordinates[0],
                PROP_AREA_LONG: coordinates[1]
            }
        )
        locations = []
        for site in self.location_cache.values():
            dist = distance.distance(coordinates,
                                 (
                                    site.lat,
                                    site.long
                                )).miles
            if dist < radius:
                locations.append({
                    **site.__dict__(),
                    "distance": dist
                })
        return locations

    async def update_area(self, area: dict):
        """Used by asyncio to update areas."""
        try:
            geocode = await geocode_reverse_lookup(
                (area[PROP_AREA_LAT], area[PROP_AREA_LONG])
            )
        except geopyexc.GeocoderTimedOut:
            _LOGGER.warning("Timeout occured while geocoding area %s.",
                            area)
            return None
        if geocode.raw["address"]["country_code"] != "gr":
            _LOGGER.debug("Skipping area %s as not in GR.",
                        area)
            return None
        self._parser_coords = (area[PROP_AREA_LAT], area[PROP_AREA_LONG])
        _LOGGER.debug("Searching FuelGR for FuelLocations at area %s",
                    area)
        response_raw = await self._send_request(
            url=FUELGR_GET_DATA.format(
                LAT=area[PROP_AREA_LAT],
                LONG=area[PROP_AREA_LONG],
                FUEL="1",
                BRAND="0",
                QUALITY="0"
            )
        )
        # convert to dict
        response_raw = xmltodict.parse(response_raw)
        # now extract fuel stations
        response_raw = response_raw["gss"]["gs"]
        _LOGGER.debug("Found %s fuel stations",
                    len(response_raw))
        
        await self.parse_response(
            response=response_raw
        )

    async def update(self, areas=None, force=None) -> list[FuelLocation]:
        """Update the cached data."""
        if self.next_update <= datetime.now() or force:
            self._configured_areas=[] if areas is None else areas
            try:
                self.next_update += self.update_interval
                coros = [self.update_area(a) for a in self._configured_areas]
                asyncio.gather(*coros)
            except Exception as exc:
                _LOGGER.error(exc)

        return list(self.location_cache.values())

    async def get_fuel_station_fuels(self, station_id) -> list[Fuel]:
        """Return a list of fuels from a fuel station."""
        response_raw = await self._send_request(
            url=FUELGR_GET_STATION_PRICES.format(
                ID=station_id
            )
        )
        # convert to dict
        response_raw = xmltodict.parse(response_raw)
        response_raw = response_raw["gsf"]["fuel"]
        _LOGGER.debug("Found %s fuels for stn %s",
                      len(response_raw),
                      station_id)
        return self.parse_fuels(response_raw)

    async def parse_raw_fuel_station(self, station: dict) -> FuelLocation:
        """Parse a single raw fuel station into FuelLocation."""
        _LOGGER.debug("Parsing object %s", station["@guid"])
        site_id = f"{self.provider_name}_{station['@id']}"
        loc = FuelLocation.create(
            site_id=site_id,
            name=station["br"]["#text"],
            address=station["ad"],
            lat=station["lt"],
            long=station["lg"],
            brand=station["br"]["#text"],
            postal_code="",
            available_fuels=await self.get_fuel_station_fuels(
                station_id=station["@id"]
            ),
            currency="EUR",
            props={
                "data": station,
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: station["@id"]
            },
            next_update=self.next_update
        )
        if site_id not in self.location_cache:
            self.location_cache[site_id] = loc
        else:
            await self.location_cache[site_id].update(loc)
        return self.location_cache[site_id]

    async def parse_response(self, response) -> list[FuelLocation]:
        """Convert fuel stations into fuel objects."""
        coros = [self.parse_raw_fuel_station(s) for s in response]
        await asyncio.gather(*coros)

    def parse_fuels(self, fuels: dict) -> list[Fuel]:
        """Parse fuels using mapping"""
        fuel_resp = []
        for f in fuels:
            fuel_resp.append(
                Fuel(
                    fuel_type=FUELGR_FUEL_TYPE_MAPPING.get(f["@type"], f["fn"]),
                    cost=float(f["pr"]),
                    props=f
                )
            )

        return fuel_resp
