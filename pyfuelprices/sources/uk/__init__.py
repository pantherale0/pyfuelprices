"""UK Fuel Sources and parsers."""

import logging
import json
import csv
from datetime import datetime

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID
)
from pyfuelprices.sources import Source, UpdateFailedError, ServiceBlocked
from pyfuelprices.fuel import Fuel
from pyfuelprices.fuel_locations import FuelLocation

_LOGGER = logging.getLogger(__name__)

class CMAParser(Source):
    """This parser is specific for the scheme by the CMA."""

    location_cache: dict[str, FuelLocation] = {}

    async def update_area(self, area):
        """Method not used."""
        raise NotImplementedError

    async def update(self, areas=None, force=False):
        """Update data."""
        if self.next_update > datetime.now() and not force:
            _LOGGER.debug("Ignoring update request")
            return
        response = await self._client_session.request(
            method=self._method,
            url=self._url,
            json=self._request_body,
            headers=self._headers
        )
        _LOGGER.debug("Update request completed for %s with status %s",
                    self.provider_name, response.status)
        if response.status == 200:
            self.next_update = datetime.now() + self.update_interval
            if "application/json" not in response.content_type:
                return await self.parse_response(
                    response=json.loads(await response.text())
                )
            if response.content_type == "text/csv":
                return await self.parse_response(
                    response=list(csv.DictReader(await response.text()))
                )
            return await self.parse_response(
                response=await response.json()
            )
        if response.status == 403:
            raise ServiceBlocked(
                status=response.status,
                response=await response.text(),
                headers=response.headers,
                service=self.provider_name
            )
        raise UpdateFailedError(
            status=response.status,
            response=await response.text(),
            headers=response.headers,
            service=self.provider_name
        )

    async def parse_response(self, response) -> list[FuelLocation]:
        """Converts CMA data into fuel price mapping."""
        for location_raw in response["stations"]:
            site_id = f"{self.provider_name}_{location_raw['site_id']}"
            location = FuelLocation.create(
                    site_id=site_id,
                    name=f"{location_raw['brand']} {location_raw['postcode']}",
                    address=location_raw["address"],
                    brand=location_raw["brand"],
                    lat=location_raw["location"]["latitude"],
                    long=location_raw["location"]["longitude"],
                    available_fuels=self.parse_fuels(location_raw["prices"]),
                    postal_code=location_raw["postcode"],
                    currency="GBP",
                    props={
                        PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                        PROP_FUEL_LOCATION_SOURCE_ID: location_raw["site_id"],
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
        f_list = []
        for f_type in fuels:
            # the following makes sure that a price is in a "normal" format
            if fuels[f_type] is not None:
                if fuels[f_type] > 10000:
                    fuels[f_type] = round(fuels[f_type]/100, 1)
                if fuels[f_type] > 1000:
                    fuels[f_type] = round(fuels[f_type]/10, 1)
                if fuels[f_type] < 100:
                    fuels[f_type] = round(fuels[f_type]*100, 1)
                fuels[f_type] = fuels[f_type] / 100 # fix "unit" issue
            f_list.append(Fuel(
                fuel_type=f_type,
                cost=fuels[f_type],
                props={}
            ))
        return f_list
