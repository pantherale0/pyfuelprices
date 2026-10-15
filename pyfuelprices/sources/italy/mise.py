"""Italy MISE Osservaprezzi Carburanti data source."""

import logging
from datetime import datetime, timedelta

from pyfuelprices.const import (
    DESKTOP_USER_AGENT,
    PROP_AREA_LAT,
    PROP_AREA_LONG,
    PROP_AREA_RADIUS,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_SOURCE_ID,
)
from pyfuelprices.fuel_locations import Fuel, FuelLocation
from pyfuelprices.helpers import geocoder, geopyexc
from pyfuelprices.sources import Source

from .const import CONST_MISE_GET_SERVICEAREA, CONST_MISE_SEARCH_ZONE

_LOGGER = logging.getLogger(__name__)


class MiseSource(Source):
    """MISE Osservaprezzi Carburanti Source (Italy)."""

    country_code = "IT"

    _headers = {"User-Agent": DESKTOP_USER_AGENT, "Content-Type": "application/json"}
    provider_name = "mise"
    update_interval = timedelta(days=1)
    # Tracks raw site IDs whose detail has already been fetched, so the
    # rate-limited detail endpoint is hit at most once per location.
    _enriched_ids: set[str] = set()

    async def _send_zone_request(self, lat, lng, radius):
        """Send a zone search request to the API for a given point and radius."""
        radius = radius * 1.609344  # convert miles to km
        payload = {"points": [{"lat": lat, "lng": lng}], "radius": radius}
        _LOGGER.debug("Sending request to MISE: %s", CONST_MISE_SEARCH_ZONE)
        async with self._client_session.post(CONST_MISE_SEARCH_ZONE, json=payload, headers=self._headers) as response:
            if response.ok:
                return await response.json()
            _LOGGER.error("Error sending request to %s: %s", CONST_MISE_SEARCH_ZONE, response)

    async def _send_detail_request(self, site_id):
        """Send a request to the API for the detail of a single service area."""
        url = CONST_MISE_GET_SERVICEAREA.format(SERVICE_AREA_ID=site_id)
        _LOGGER.debug("Sending request to MISE: %s", url)
        async with self._client_session.get(url, headers=self._headers) as response:
            if response.ok:
                return await response.json()
            _LOGGER.error("Error sending request to %s: %s", url, response)

    async def get_site(self, site_id) -> FuelLocation:
        """Return an individual fuel location, enriching it from the detail endpoint.

        The detail endpoint is aggressively rate-limited, so it is fetched at most
        once per location (tracked in ``_enriched_ids``); afterwards the cached
        location (already populated with prices by the zone search) is returned.
        """
        raw_id = str(site_id)
        if raw_id.startswith(f"{self.provider_name}_"):
            raw_id = raw_id[len(self.provider_name) + 1 :]
        cached = self.location_cache.get(f"{self.provider_name}_{raw_id}")
        if cached is None:
            raise ValueError(f"Site {site_id} is not available in the cache.")
        if raw_id not in self._enriched_ids:
            self._enriched_ids.add(raw_id)
            detail = await self._send_detail_request(raw_id)
            if detail is not None:
                refreshed = self._parse_detail(detail, cached)
                await cached.update(refreshed)
                cached.props.update(refreshed.props)
        return cached

    async def search_sites(self, coordinates, radius: float) -> list[dict]:
        """Return all available sites within a given radius."""
        # first query the cache; force an area update if no data is available.
        data = await super().search_sites(coordinates, radius)
        if len(data) > 0:
            return data
        await self.update(
            areas=[{PROP_AREA_LAT: coordinates[0], PROP_AREA_LONG: coordinates[1], PROP_AREA_RADIUS: radius}],
            force=True,
        )
        return await super().search_sites(coordinates, radius)

    async def update_area(self, area) -> bool:
        """Update a given area."""
        try:
            geocode = await geocoder.geocode_reverse_lookup((area[PROP_AREA_LAT], area[PROP_AREA_LONG]))
        except geopyexc.GeocoderTimedOut:
            _LOGGER.warning("Timeout occured while geocoding area %s.", area)
            return False
        if geocode.raw["address"]["country_code"] != "it":
            _LOGGER.debug("Skipping area %s as not in IT.", area)
            return False
        response_raw = await self._send_zone_request(
            lat=area[PROP_AREA_LAT], lng=area[PROP_AREA_LONG], radius=area[PROP_AREA_RADIUS]
        )
        if response_raw is not None and response_raw.get("success"):
            await self.parse_response(response_raw.get("results", []))
            return True
        _LOGGER.error("Error sending request to %s: %s", self.provider_name, response_raw)
        return False

    def _parse_raw(self, station: dict) -> FuelLocation:
        """Parse a single raw instance of a fuel site."""
        site_id = f"{self.provider_name}_{station['id']}"
        _LOGGER.debug("Parsing MISE location ID %s", site_id)
        loc = FuelLocation.create(
            site_id=site_id,
            name=station["name"],
            address=station.get("address") or "",
            lat=station["location"]["lat"],
            long=station["location"]["lng"],
            brand=station["brand"],
            available_fuels=self.parse_fuels(station["fuels"]),
            currency="EUR",
            props={
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: station["id"],
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                "insert_date": station.get("insertDate"),
            },
        )
        loc.next_update = (
            self.next_update if self.next_update > datetime.now() else (self.next_update + self.update_interval)
        )
        return loc

    def _parse_detail(self, detail: dict, cached: FuelLocation) -> FuelLocation:
        """Parse a service area detail response into a FuelLocation."""
        loc = FuelLocation.create(
            site_id=cached.id,
            name=detail["name"],
            address=detail.get("address", cached.address),
            lat=cached.lat,
            long=cached.long,
            brand=detail.get("brand", cached.brand),
            available_fuels=self.parse_fuels(detail.get("fuels", [])),
            currency="EUR",
            props={
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: detail["id"],
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                "insert_date": detail["fuels"][0].get("insertDate") if detail.get("fuels") else None,
                "phone_number": detail.get("phoneNumber"),
                "email": detail.get("email"),
                "website": detail.get("website"),
                "company": detail.get("company"),
                "services": [service.get("description") for service in detail.get("services", [])],
                "opening_hours": detail.get("orariapertura", []),
            },
        )
        loc.next_update = (
            self.next_update if self.next_update > datetime.now() else (self.next_update + self.update_interval)
        )
        return loc

    async def parse_response(self, response) -> list[FuelLocation]:
        for station_raw in response:
            station = self._parse_raw(station_raw)
            if station.id not in self.location_cache:
                self.location_cache[station.id] = station
            else:
                await self.location_cache[station.id].update(station)
        return list(self.location_cache.values())

    def parse_fuels(self, fuels: list[dict]) -> list[Fuel]:
        """Parse fuel data from MISE."""
        fuels_parsed = []
        for fuel in fuels:
            fuels_parsed.append(
                Fuel(
                    fuel_type=str(fuel["name"]),
                    cost=fuel["price"],
                    props={"self_service": bool(fuel.get("isSelf", False)), "validity_date": fuel.get("validityDate")},
                )
            )
        return fuels_parsed
