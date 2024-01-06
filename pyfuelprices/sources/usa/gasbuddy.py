"""GasBuddy USA data source."""
import logging
import json
import uuid

# use these-united-states for geocoding to states
import united_states
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
from pyfuelprices.sources import Source

_LOGGER = logging.getLogger(__name__)

CONST_GASBUDDY_STATIONS_FMT = (
    "https://services.gasbuddy.com/mobile-orchestration/stations?authid={AUTHID}"
    "&country={COUNTRY}&distance_format={DISTANCEFMT}&limit={LIMIT}&region={STATE}"
    "&lat={LAT}&lng={LONG}"
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
    _usa = united_states.UnitedStates()
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

    async def search_sites(self, coordinates, radius: float) -> list[FuelLocation]:
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
            if distance.distance(coordinates,
                                 (
                                    site.lat,
                                    site.long
                                )).miles < radius:
                locations.append(site)
        return locations

    async def update(self, areas=None) -> list[FuelLocation]:
        """Custom update handler as this needs to query GasBuddy on areas."""
        self._configured_areas=[] if areas is None else areas
        for area in self._configured_areas:
            self._parser_coords = (area[PROP_AREA_LAT], area[PROP_AREA_LONG])
            self._parser_radius = area[PROP_AREA_RADIUS]
            coord_data = self._usa.from_coords(
                lat=area[PROP_AREA_LAT],
                lon=area[PROP_AREA_LONG]
            )
            if len(coord_data) > 0:
                _LOGGER.debug("Searching GasBuddy for FuelLocations at area %s",
                              area)
                coord_data = coord_data[0]
                response_raw = await self._send_request(
                    url=CONST_GASBUDDY_STATIONS_FMT.format(
                        AUTHID=str(uuid.uuid4()),
                        COUNTRY="US",
                        DISTANCEFMT="auto",
                        LIMIT=1000,
                        STATE=coord_data.abbr,
                        LAT=area[PROP_AREA_LAT],
                        LONG=area[PROP_AREA_LONG]
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
            }
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
