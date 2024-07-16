"""GasBuddy USA data source."""
import logging
import json
import uuid

from geopy import distance

from pyfuelprices.fuel_locations import Fuel, FuelLocation

from pyfuelprices.const import (
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID,
    ANDROID_USER_AGENT
)
from pyfuelprices.helpers import geocode_reverse_lookup, get_bounding_box
from pyfuelprices.sources import Source

_LOGGER = logging.getLogger(__name__)

CONST_GASBUDDY_STATIONS_FMT = (
    "https://services.gasbuddy.com/mobile-orchestration/stations?authid={AUTHID}"
    "&country={COUNTRY}&distance_format={DISTANCEFMT}&limit={LIMIT}"
    "&lat={LAT}&lng={LONG}"
    "&location_specification={MIN_LAT}%2C{MIN_LON}%2C{MAX_LAT}%2C{MAX_LON}"
)
CONST_GASBUDDY_GET_STATION_FMT = (
    "https://services.gasbuddy.com/mobile-orchestration/stations/{STATIONID}"
    "?authid={AUTHID}"
)

class GasBuddyUSASource(Source):
    """GasBuddy USA data source."""

    _headers = {
        "apikey": "56c57e8f1132465d817d6a753c59387e",
        "User-Agent": ANDROID_USER_AGENT
    }
    _parser_radius = 0
    _parser_coords = ()
    provider_name = "gasbuddy"
    location_cache = {}

    async def _send_request(self, url) -> str:
        """Send a request to the API and return the raw response."""
        _LOGGER.debug("Sending HTTP request to GasBuddy with URL %s", url)
        async with self._client_session.get(url=url,
                                            headers=self._headers) as response:
            if response.ok:
                return await response.text()
            _LOGGER.error("Error sending request to %s: %s",
                            url,
                            response)

    async def get_site(self, site_id) -> FuelLocation:
        """Return the site from the location cache."""
        if site_id in self.location_cache:
            return self.location_cache[site_id]
        if "_" in str(site_id):
            site_id = site_id.split("_")
        response_raw = await self._send_request(
            url=CONST_GASBUDDY_GET_STATION_FMT.format(
                STATIONID=str(site_id),
                AUTHID=str(uuid.uuid4)
            )
        )
        return await self.parse_raw_fuel_station(
            station=json.loads(response_raw)["station"]
        )

    async def search_sites(self, coordinates, radius: float) -> list[dict]:
        """Return all available sites within a given radius."""
        # first query the API to populate cache / update data in case this data is unavailable.
        await self.update(
            areas=[{
                PROP_AREA_LAT: coordinates[0],
                PROP_AREA_LONG: coordinates[1],
                PROP_AREA_RADIUS: radius
            }]
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

    async def update(self, areas=None, force=None) -> list[FuelLocation]:
        """Custom update handler as this needs to query GasBuddy on areas."""
        self._configured_areas=[] if areas is None else areas
        for area in self._configured_areas:
            self._parser_coords = (area[PROP_AREA_LAT], area[PROP_AREA_LONG])
            self._parser_radius = area[PROP_AREA_RADIUS]
            geocoded = await geocode_reverse_lookup(self._parser_coords)
            if geocoded is None:
                _LOGGER.debug("Geocode failed, skipping area %s", area)
                continue
            if geocoded.raw["address"]["country_code"] not in ["us", "ca"]:
                _LOGGER.debug("Geocode not within USA, skipping area %s", area)
                continue
            _LOGGER.debug("Searching GasBuddy for FuelLocations at area %s",
                            area)
            bbox = get_bounding_box(area[PROP_AREA_LAT],
                                    area[PROP_AREA_LONG],
                                    area[PROP_AREA_RADIUS])
            response_raw = await self._send_request(
                url=CONST_GASBUDDY_STATIONS_FMT.format(
                    AUTHID=str(uuid.uuid4()),
                    COUNTRY="US",
                    DISTANCEFMT="auto",
                    LIMIT=1000,
                    LAT=area[PROP_AREA_LAT],
                    LONG=area[PROP_AREA_LONG],
                    MIN_LAT=bbox.lat_min,
                    MIN_LON=bbox.lon_min,
                    MAX_LAT=bbox.lat_max,
                    MAX_LON=bbox.lon_max
                )
            )
            await self.parse_response(json.loads(response_raw))
        return list(self.location_cache.values())

    async def parse_raw_fuel_station(self, station) -> FuelLocation:
        """Converts a raw instance of a fuel station into a fuel location."""
        info = station["info"]
        site_id = f"{self.provider_name}_{station['id']}"
        _LOGGER.debug("Parsing GasBuddy location ID %s", site_id)
        loc = FuelLocation.create(
            site_id=site_id,
            name=f"{info['name']} {info['address']['postal_code']}",
            address="See properties",
            lat=info["latitude"],
            long=info["longitude"],
            brand=info["brand_name"],
            available_fuels=self.parse_fuels(station["fuel_products"]),
            postal_code=info['address']['postal_code'],
            currency="USD",
            props={
                "data": station,
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: station["id"]
            },
            next_update=self.next_update
        )
        if site_id not in self.location_cache:
            self.location_cache[site_id] = loc
        else:
            await self.location_cache[site_id].update(loc)
        return self.location_cache[site_id]

    async def parse_response(self, response) -> list[FuelLocation]:
        if response.get("stations", None) is not None:
            response = response["stations"]
        for station in response:
            info = station["info"]
            if distance.distance(
                self._parser_coords,
                (info["latitude"], info["longitude"])
            ).miles <= self._parser_radius:
                await self.parse_raw_fuel_station(station=station)

        return list(self.location_cache.values())

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Parse fuels from fuel_products."""
        fuel_parsed = []
        for fuel in fuels:
            cost = fuel.get("cash",
                            fuel.get("credit", None))
            fuel_parsed.append(Fuel(
                fuel_type=fuel["fuel_product"],
                cost=0 if cost is None else cost["price"],
                props=fuel
            ))
        return fuel_parsed
