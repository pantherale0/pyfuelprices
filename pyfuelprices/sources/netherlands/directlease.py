"""DirectLease data source."""

import random
import re
import logging
import uuid
import hashlib
from datetime import datetime, timedelta
from time import time

import aiohttp

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_DYNAMIC_BUILD,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_SOURCE_ID,
    ANDROID_USER_AGENT
)
from pyfuelprices.sources import ServiceBlocked, Source, UpdateFailedError
from pyfuelprices.fuel_locations import Fuel, FuelLocation

from .const import DIRECTLEASE_API_PLACES, DIRECTLEASE_API_STATION

_LOGGER = logging.getLogger(__name__)


def _hash(hsh: str):
    encoded_string = hsh.encode("utf-8")
    hash_object = hashlib.sha1(encoded_string)
    return hash_object.hexdigest()

def _checksum_generator(url: str) -> str:
    """Generate a directlease API checksum."""
    # first generate a dummy device identifier
    date_string = datetime.now().strftime("%Y%m%d")
    device_uuid = str(uuid.uuid4())
    date_uuid_part = f"{date_string}_{device_uuid}"
    timestamp = int(time())
    parts = url.split("/")
    file_path = "/".join(parts[3:])
    file_path = f"/{file_path}"
    base_string = f"{date_uuid_part}/{timestamp}/{file_path}/X-Checksum"
    return f"{date_uuid_part}/{timestamp}/{_hash(base_string)}"

class DirectLeaseFuelLocation(FuelLocation):
    """DirectLease custom fuel location."""

    next_update: datetime = datetime.now()
    _client_session: aiohttp.ClientSession

    @classmethod
    def create(cls,
               site_id: str,
               name: str,
               address: str,
               lat: float,
               long: float,
               brand: str,
               available_fuels,
               last_updated: datetime = datetime.now(),
               postal_code: str | None = None,
               currency: str = "",
               props: dict = None,
               client_session: aiohttp.ClientSession = None
        ) -> 'FuelLocation':
        """Create an instance of fuel location."""
        location = cls()
        location._id = site_id
        location._address = address
        location._name = name
        location.lat = lat
        location.long = long
        location._brand = brand
        location.available_fuels = available_fuels
        location._postal_code = postal_code
        location._currency = currency
        location.last_updated = last_updated
        location.props = props
        location._client_session = client_session
        return location

    async def dynamic_build_fuels(self):
        """Dynamic requests to build fuels."""
        _LOGGER.debug("Update requested for station %s", self._id)
        if (len(self.available_fuels) != 0 and self.next_update > datetime.now()):
            _LOGGER.debug("Update skipped, next update required at %s, current fuel count %s",
                          self.next_update,
                          len(self.available_fuels))
            return None

        request_url = DIRECTLEASE_API_STATION.format(
            station_id=self.props[PROP_FUEL_LOCATION_SOURCE_ID]
        )

        _LOGGER.debug("Requesting fuel prices for station %s (%s)", self._id, request_url)

        try:
            async with self._client_session.request(
            method="GET",
            url=request_url,
            headers={
                "X-Checksum": _checksum_generator(request_url),
                "User-Agent": ANDROID_USER_AGENT
            }) as response:
                _LOGGER.debug("Got status code %s for dynamic parse of site %s",
                                response.status,
                                self.props[PROP_FUEL_LOCATION_SOURCE_ID])
                if response.status == 200:
                    response = await response.json()
                    # opportunity to build extra location data too
                    self._postal_code = response.get("postalCode", "Unknown")
                    self._address = response.get("address", "Unknown")
                    self._brand = response.get("brand", "Unknown")
                    self._name = response.get("name", "Unknown")
                    for fuel_raw in response["fuels"]:
                        _LOGGER.debug("Parsing fuel %s", fuel_raw)
                        f_type = re.search(r"\(([^)]+)\)", fuel_raw["name"])
                        if f_type is None:
                            f_type = fuel_raw["name"].upper()
                        else:
                            f_type = f_type.group(1).upper()
                        try:
                            fuel_cost = fuel_raw.get("price", None)
                            if fuel_cost is not None:
                                self.get_fuel(f_type).update(
                                    fuel_type=f_type,
                                    cost=fuel_raw["price"]/1000,
                                    props={}
                                )
                            else:
                                self.get_fuel(f_type).update(
                                    fuel_type=f_type,
                                    cost=0,
                                    props={
                                        "unavailable": True
                                    }
                                )
                        except ValueError:
                            if fuel_raw.get("price", None) is not None:
                                self.available_fuels.append(
                                    Fuel(
                                        fuel_type=f_type,
                                        cost=fuel_raw["price"]/1000,
                                        props={}
                                    )
                                )
                elif response.status == 403:
                    # 403 for directlease is an IP block
                    _LOGGER.error(
                        ("DirectLease appears to have blocked your IP. Your options are:"
                        "1) Contact tankservice-block@app-it-up.com for further support. "
                        "2) Change your WAN IP address or use a VPN. "
                        "3) Use a proxy server to connect. "))

            self.next_update = datetime.now() + timedelta(
            days=1,
            minutes=random.randint(1,240),
            seconds=random.randint(1,60)) # prevent overloading the API and IP lockouts

        except aiohttp.ServerDisconnectedError as err:
            _LOGGER.warning("Error sending request to URL %s: %s",
                            request_url,
                            err)

class DirectLeaseTankServiceParser(Source):
    """DirectLease parser for Belgium/Netherlands data."""

    _url = DIRECTLEASE_API_PLACES
    update_interval = timedelta(days=1) # update once per day to prevent API spam.
    provider_name = "directlease"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None

    async def get_site(self, site_id) -> FuelLocation:
        await self.location_cache[site_id].dynamic_build_fuels()
        return self.location_cache[site_id]

    async def update(self, areas=None, force=None) -> list[FuelLocation]:
        try:
            await super().update(areas)
        except UpdateFailedError as err:
            if err.status == 403:
                # 403 for directlease is an IP block
                _LOGGER.error(("DirectLease appears to have blocked your IP. Your options are:"
                                "1) Contact tankservice-block@app-it-up.com for further support. "
                                "2) Change your WAN IP address or use a VPN. "
                                "3) Use a proxy server to connect. "))
                raise ServiceBlocked(err.status, err.response, err.headers) from err

        self.next_update = datetime.now() + timedelta(
            days=1,
            minutes=random.randint(1,240),
            seconds=random.randint(1,60)) # prevent overloading the API and IP lockouts
        return list(self.location_cache.values())

    async def parse_response(self, response) -> list[DirectLeaseFuelLocation]:
        """Fuel location parser for DirectLease."""
        for raw_loc in response:
            site_id = f"directlease_{raw_loc['id']}"
            if site_id not in self.location_cache:
                _LOGGER.debug("Parsing DirectLease location ID %s", site_id)
                loc = DirectLeaseFuelLocation.create(
                    site_id=site_id,
                    name=raw_loc.get("name", None),
                    address="Unknown",
                    lat=raw_loc["lat"],
                    long=raw_loc["lng"],
                    brand=raw_loc.get("brand", None),
                    available_fuels=[],
                    postal_code="Unknown",
                    currency="EUR",
                    props={
                        PROP_FUEL_LOCATION_DYNAMIC_BUILD: True,
                        PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                        PROP_FUEL_LOCATION_SOURCE_ID: raw_loc["id"]
                    },
                    last_updated=datetime.now(),
                    client_session=self._client_session
                )
                if (loc.name is None and loc.brand is not None):
                    loc.name = raw_loc["brand"] + " " + raw_loc["city"]
                if loc.name is None:
                    loc.name = f"Unknown site {loc.props[PROP_FUEL_LOCATION_SOURCE_ID]}"
                if loc.brand is None:
                    loc.brand = "Unknown"
                self.location_cache[site_id] = loc

        for site in self.location_cache.values():
            if (self._check_if_coord_in_area((
                    site.lat, site.long)) or (
                    len(site.available_fuels)>0
                )):
                await site.dynamic_build_fuels()

        return list(self.location_cache.values())

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Fuel parser not required for this module."""
