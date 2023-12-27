"""Belgium and Netherlands Fuel Sources and parsers."""

import re
import logging
import uuid
import hashlib
from datetime import datetime, timedelta
from time import time

import aiohttp

from pyfuelprices.const import CONF_FUEL_LOCATION_DYNAMIC_BUILD
from pyfuelprices.sources import Source
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

    dl_stn_id = 0
    update_interval = timedelta(days=1) # prevents over loading the API.
    next_update: datetime = datetime.now()
    currency = "EUR"

    async def dynamic_build_fuels(self):
        """Dynamic requests to build fuels."""
        if (len(self.available_fuels) != 0 and self.next_update > datetime.now()):
            return None
        request_url = DIRECTLEASE_API_STATION.format(station_id=self.dl_stn_id)

        session = aiohttp.ClientSession()
        response = await session.request(
            method="GET",
            url=request_url,
            headers={
                "X-Checksum": _checksum_generator(request_url)
            }
        )
        _LOGGER.debug("Got status code %s for dynamic parse of site %s",
                        response.status,
                        self.dl_stn_id)
        if response.status == 200:
            response = await response.json()
            # opportunity to build extra location data too
            self.postal_code = response.get("postalCode", "Unknown")
            self.address = response.get("address", "Unknown")
            self.brand = response.get("brand", "Unknown")
            self.name = response.get("name", "Unknown")
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
                            cost="Unavailable",
                            props={}
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

        await session.close()
        self.next_update = datetime.now()+self.update_interval

class DirectLeaseTankServiceParser(Source):
    """DirectLease parser for Netherlands data."""

    _url = DIRECTLEASE_API_PLACES
    update_interval = timedelta(days=1) # update once per day due to expensive OCR operations.

    def parse_response(self, response) -> list[DirectLeaseFuelLocation]:
        """Fuel location parser for DirectLease."""
        parsed = []
        for raw_loc in response:
            _LOGGER.debug("Parsing DirectLease location ID %s", raw_loc["id"])
            loc = DirectLeaseFuelLocation()
            loc.id = f"directlease_{raw_loc['id']}"
            loc.dl_stn_id = raw_loc["id"]
            loc.props[CONF_FUEL_LOCATION_DYNAMIC_BUILD] = True
            loc.lat = raw_loc["lat"]
            loc.long = raw_loc["lng"]
            loc.brand = raw_loc.get("brand", None)
            loc.name = raw_loc.get("name", None)
            if (loc.name is None and loc.brand is not None):
                loc.name = raw_loc["brand"] + " " + raw_loc["city"]
            if loc.name is None:
                loc.name = f"Unknown site {loc.dl_stn_id}"
            if loc.brand is None:
                loc.brand = "Unknown"
            loc.address = "Unknown"
            loc.postal_code = "Unknown"
            loc.last_updated = datetime.now()
            loc.next_update = datetime.now()-timedelta(seconds=1) # force next update
            parsed.append(loc)
        return parsed

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Fuel parser not required for this module."""
