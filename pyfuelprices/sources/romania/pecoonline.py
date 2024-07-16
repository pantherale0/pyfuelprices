"""PecoOnline Service for Romania."""

import logging
import uuid
import json
from datetime import timedelta

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID
)
from pyfuelprices.sources import Source
from pyfuelprices.fuel_locations import Fuel, FuelLocation

from .const import (
    PECO_STANDARD_HEADERS,
    PECO_ONLINE_API,
    PECO_QUERY_CLAUSE,
    PECO_FUEL_MAPPING
)

_LOGGER = logging.getLogger(__name__)

class PecoOnlineSource(Source):
    """The root Peco Online data source."""

    _url = PECO_ONLINE_API
    update_interval = timedelta(days=1) # update once per day to prevent API spam.
    provider_name = "pecoonline"
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None
    _headers = PECO_STANDARD_HEADERS

    async def _send_request(self, url, body) -> str:
        """Send a request to the API and return the raw response."""
        _LOGGER.debug("Sending HTTP request to PecoOnline with URL %s", url)
        if self._headers["X-Parse-Installation-Id"] is None:
            self._headers["X-Parse-Installation-Id"] = str(uuid.uuid4())
        async with self._client_session.post(url=url,
                                             json=body,
                                            headers=self._headers) as response:
            if response.ok:
                return await response.text()
            _LOGGER.error("Error sending request to %s: %s",
                            url,
                            response)

    async def get_site(self, site_id) -> FuelLocation:
        """Return a single site."""
        return self.location_cache[site_id]

    async def update(self, areas=None, force=None) -> list[FuelLocation]:
        """Update the cached data."""
        try:
            response_raw = await self._send_request(
                url=self._url,
                body={
                    "limit": 100000,
                    "where": PECO_QUERY_CLAUSE,
                    "order": "Benzina_Regular",
                    "_method": "GET"
                }
            )
            await self.parse_response(
                response=json.loads(response_raw)
            )
        except Exception as exc:
            _LOGGER.error(exc)

        return list(self.location_cache.values())

    async def parse_raw_fuel_station(self, station: dict) -> FuelLocation:
        """Parse a single raw fuel station into FuelLocation."""
        site_id = f"{self.provider_name}_{station['objectId']}"
        loc = FuelLocation.create(
            site_id=site_id,
            name=station["Statie"],
            address=station["Adresa"],
            lat=station["lat"],
            long=station["lng"],
            brand=station["Retea"],
            postal_code="See address",
            available_fuels=self.parse_fuels(station),
            currency="RON",
            props={
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: station['objectId']
            }
        )
        if site_id not in self.location_cache:
            self.location_cache[site_id] = loc
        else:
            await self.location_cache[site_id].update(loc)
        return self.location_cache[site_id]

    async def parse_response(self, response) -> list[FuelLocation]:
        """Convert fuel stations into fuel objects."""
        for result in response["results"]:
            _LOGGER.debug("Parsing object %s", result["objectId"])
            await self.parse_raw_fuel_station(result)

    def parse_fuels(self, fuels: dict) -> list[Fuel]:
        """Parse fuels using mapping"""
        fuel_resp = []
        for k, v in PECO_FUEL_MAPPING.items():
            if k in fuels:
                fuel_resp.append(
                    Fuel(
                        fuel_type=v,
                        cost=fuels[k],
                        props=None
                    )
                )

        return fuel_resp
