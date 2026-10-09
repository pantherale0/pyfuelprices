"""Official ANWB onderweg Fuel Data Source."""

# This is an official data source for Home Assistant users from Finelly
import logging

from geopy import (
    distance,
    point
)

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_DYNAMIC_BUILD,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_SOURCE_ID,
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS
)
from pyfuelprices.fuel_locations import FuelLocation, Fuel
from pyfuelprices.sources import Source, UpdateFailedError

from .const import ANWB_API_BASE

_LOGGER = logging.getLogger(__name__)

# Each split quarters the box, so this caps a single area at 4 ** 3 requests.
ANWB_MAX_SPLIT_DEPTH = 3

class ANWBOnderwegDataSource(Source):
    """Core ANWB onderweg source."""

    country_code = ["CH", "DE", "DK", "ES", "FI", "GB", "FR", "IT", "NO", "NL", "PT", "RU", "SE", "TR", "UA", "LU"]

    provider_name="anwbonderweg"
    location_cache: dict[str, FuelLocation] = {}
    auto_country_mapping = False

    @staticmethod
    def _build_bounding_box(lat: float, long: float, radius: float) -> tuple[float, float, float, float]:
        """Return (min_lat, min_lon, max_lat, max_lon) for a radius in miles."""
        center = point.Point(lat, long)
        dist = distance.distance(miles=radius)
        return (
            dist.destination(center, 180).latitude,
            dist.destination(center, 270).longitude,
            dist.destination(center, 0).latitude,
            dist.destination(center, 90).longitude,
        )

    async def update_area(self, area: dict) -> bool:
        """Update a given area."""
        await self._fetch_box(
            self._build_bounding_box(
                lat=area[PROP_AREA_LAT],
                long=area[PROP_AREA_LONG],
                radius=area[PROP_AREA_RADIUS]
            )
        )
        return True

    async def _fetch_box(self, box: tuple[float, float, float, float], depth: int = 0):
        """Fetch stations in a bounding box, splitting it if the API reports too many results."""
        min_lat, min_lon, max_lat, max_lon = box
        url = f"{ANWB_API_BASE}&bounding-box-filter={min_lat}%2C{min_lon}%2C{max_lat}%2C{max_lon}"
        async with self._client_session.get(url=url) as response:
            if not response.ok:
                raise UpdateFailedError(
                    status=response.status,
                    response=await response.text(),
                    headers=response.headers,
                    service=self.provider_name
                )
            data = await response.json()
            status = response.status
            headers = response.headers

        error = data.get("error")
        if error is None:
            await self.parse_response(data)
            return
        if error.get("code") == "limit_exceeded" and depth < ANWB_MAX_SPLIT_DEPTH:
            _LOGGER.debug("ANWB limit exceeded for box %s, splitting (depth %s)", box, depth + 1)
            mid_lat = (min_lat + max_lat) / 2
            mid_lon = (min_lon + max_lon) / 2
            for sub_box in (
                (min_lat, min_lon, mid_lat, mid_lon),
                (min_lat, mid_lon, mid_lat, max_lon),
                (mid_lat, min_lon, max_lat, mid_lon),
                (mid_lat, mid_lon, max_lat, max_lon),
            ):
                await self._fetch_box(sub_box, depth + 1)
            return
        raise UpdateFailedError(
            status=status,
            response=str(error),
            headers=headers,
            service=self.provider_name
        )

    async def search_sites(self, coordinates, radius: float) -> list[dict]:
        """Return all available sites within the bounding-box-filter"""
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

    async def parse_response(self, response: dict):
        """Parse response data."""
        i = 0
        for station in response.get("value") or []:
            await self.parse_fuel_station(station)
            i += 1
            if i % 100 == 1:
                _LOGGER.debug("%s stations loaded", i)
        return list(self.location_cache.values())

    async def parse_fuel_station(self, data: dict):
        """Parse a given fuel station and load into cache."""
        site_id = f"{self.provider_name}_{data['id']}"
        address = data.get("address")
        coordinates = data.get("coordinates")  
        loc = FuelLocation.create(
            site_id=site_id,
            name=data.get("title", None),
            address=f"{address.get("streetAddress")}, {address.get("city")}",
            lat=coordinates.get("latitude"),
            long=coordinates.get("longitude"),
            brand=None,
            available_fuels=self.parse_fuels(data.get("prices")),
            postal_code=f"{data.get("address").get("postalCode")}" ,
            currency="EUR",
            props={
                PROP_FUEL_LOCATION_DYNAMIC_BUILD: False,
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: data["id"]
            },
        )
        loc.next_update = self.next_update + self.update_interval
        if site_id not in self.location_cache:
            self.location_cache[site_id] = loc
        else:
            await self.location_cache[site_id].update(loc)
        return self.location_cache[site_id]



    #    EURO95 = E10
    #    EURO98 = E5
    #    DIESEL = B7
    #    AUTOGAS = LPG
    #    Premium diesel = ?

    def parse_fuels(self, fuels) -> list[Fuel]:
        parsed = []
        if fuels:
            for fuel in fuels:
                parsed.append(Fuel(fuel_type=fuel.get("fuelType"), cost=fuel.get("value")))
        return parsed
