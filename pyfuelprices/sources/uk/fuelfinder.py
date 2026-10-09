"""UK Government Fuel Finder data source."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import voluptuous as vol

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID
)
from pyfuelprices.enum import SupportsConfigType
from pyfuelprices.fuel_locations import Fuel, FuelLocation
from pyfuelprices.sources import Source, UpdateFailedError, ServiceBlocked

from .const import (
    CONST_FUELFINDER_BASE,
    CONST_FUELFINDER_TOKEN,
    CONST_FUELFINDER_REFRESH,
    CONST_FUELFINDER_STATIONS,
    CONST_FUELFINDER_PRICES,
    CONST_FUELFINDER_PAGE_SIZE,
    CONST_FUELFINDER_FUEL_MAP
)

_LOGGER = logging.getLogger(__name__)

CONFIG = vol.Schema(
    {
        vol.Required("client_id"): str,
        vol.Required("client_secret"): str
    }
)

# The API allows 100 requests per minute and only one request in flight per client.
REQUEST_GAP = 0.7
MAX_ATTEMPTS = 4
FULL_RESYNC_INTERVAL = timedelta(hours=24)
INCREMENTAL_OVERLAP = timedelta(minutes=30)
TOKEN_EXPIRY_MARGIN = timedelta(minutes=2)
RETRYABLE_STATUS = (429, 500, 502, 503, 504)


def _unwrap(body) -> list[dict]:
    """Responses may be a bare list or wrapped in a data envelope."""
    if isinstance(body, dict):
        body = body.get("data", [])
    return body if isinstance(body, list) else []


def _parse_price(raw) -> float | None:
    """Convert a Fuel Finder price into GBP per litre."""
    try:
        price = float(raw)
    except (TypeError, ValueError):
        return None
    if price <= 0:
        return None
    # Most retailers submit pence per litre, some submit pounds per litre.
    if price < 10:
        return round(price, 4)
    return round(price / 100, 4)


def _parse_float(raw) -> float | None:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


class FuelFinderUKSource(Source):
    """UK Government Fuel Finder source."""

    country_code = "GB"
    provider_name = "fuelfinder"
    attr_config_type = SupportsConfigType.REQUIRES_ONLY
    attr_config = CONFIG
    auto_country_mapping = False

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._access_token: str | None = None
        self._access_expires: datetime | None = None
        self._refresh_token: str | None = None
        self._refresh_expires: datetime | None = None
        self._stations: dict[str, dict] = {}
        self._prices: dict[str, dict[str, Fuel]] = {}
        self._stations_cursor: datetime | None = None
        self._prices_cursor: datetime | None = None
        self._last_full_sync: datetime | None = None
        self._update_lock = asyncio.Lock()

    async def search_sites(self, coordinates, radius: float) -> list[dict]:
        """Return all available sites within a given radius."""
        if not self._stations:
            await self.update(force=True)
        return await super().search_sites(coordinates, radius)

    async def update_area(self, area: dict) -> bool:
        """Method not used, Fuel Finder is updated nationally."""
        raise NotImplementedError

    async def update(self, areas=None, force=False) -> list[FuelLocation]:
        """Update stations and prices from Fuel Finder."""
        if self.next_update > datetime.now() and not force:
            _LOGGER.debug("Ignoring update request")
            return
        async with self._update_lock:
            now = datetime.now(timezone.utc)
            if (self._last_full_sync is None
                    or now - self._last_full_sync > FULL_RESYNC_INTERVAL):
                self._stations_cursor = None
                self._prices_cursor = None

            stations = await self._fetch_all(CONST_FUELFINDER_STATIONS, self._stations_cursor)
            prices = await self._fetch_all(CONST_FUELFINDER_PRICES, self._prices_cursor)

            if self._stations_cursor is None:
                self._last_full_sync = now
            self._stations_cursor = now
            self._prices_cursor = now
            self.next_update = datetime.now() + self.update_interval

            changed: set[str] = set()
            for station in stations:
                if node_id := station.get("node_id"):
                    self._stations[node_id] = station
                    changed.add(node_id)
            for station in prices:
                if node_id := station.get("node_id"):
                    self._parse_station_prices(node_id, station.get("fuel_prices") or [])
                    changed.add(node_id)

            for node_id in changed:
                await self._build_location(node_id)
            _LOGGER.debug("Fuel Finder update complete, %s stations changed", len(changed))
        return list(self.location_cache.values())

    def _parse_station_prices(self, node_id: str, fuel_prices: list[dict]):
        """Store the latest known price for each fuel at a station."""
        known = self._prices.setdefault(node_id, {})
        for entry in fuel_prices:
            cost = _parse_price(entry.get("price"))
            if cost is None or not entry.get("fuel_type"):
                continue
            fuel_type = CONST_FUELFINDER_FUEL_MAP.get(entry["fuel_type"], entry["fuel_type"])
            known[fuel_type] = Fuel(
                fuel_type=fuel_type,
                cost=cost,
                props={
                    "fuel_finder_type": entry["fuel_type"],
                    "last_updated": entry.get("price_last_updated")
                }
            )

    async def _build_location(self, node_id: str):
        """Create or update the cached location for a station."""
        site_id = f"{self.provider_name}_{node_id}"
        station = self._stations.get(node_id)
        if station is None:
            return
        if station.get("permanent_closure"):
            self.location_cache.pop(site_id, None)
            return
        location = station.get("location") or {}
        lat = _parse_float(location.get("latitude"))
        long = _parse_float(location.get("longitude"))
        if lat is None or long is None:
            return
        address = ", ".join(
            part for part in (location.get("address_line_1"), location.get("address_line_2"))
            if part
        )
        loc = FuelLocation.create(
            site_id=site_id,
            name=station.get("trading_name") or station.get("brand_name") or "",
            address=address,
            lat=lat,
            long=long,
            brand=station.get("brand_name") or "",
            available_fuels=list(self._prices.get(node_id, {}).values()),
            postal_code=location.get("postcode"),
            currency="GBP",
            props={
                PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID: node_id,
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
                "temporary_closure": station.get("temporary_closure"),
                "is_motorway_service_station": station.get("is_motorway_service_station"),
                "is_supermarket_service_station": station.get("is_supermarket_service_station"),
                "amenities": station.get("amenities"),
                "opening_times": station.get("opening_times"),
                "public_phone_number": station.get("public_phone_number")
            },
            next_update=self.next_update
        )
        if site_id not in self.location_cache:
            self.location_cache[site_id] = loc
        else:
            await self.location_cache[site_id].update(loc)

    async def _fetch_all(self, url: str, since: datetime | None) -> list[dict]:
        """Fetch every page of a batched endpoint."""
        params = {}
        if since is not None:
            params["effective-start-timestamp"] = (
                since - INCREMENTAL_OVERLAP
            ).strftime("%Y-%m-%d %H:%M:%S")
        results = []
        batch = 1
        while True:
            page = await self._fetch_page(url, {**params, "batch-number": batch},
                                          retry_empty=since is None)
            if not page:
                break
            results.extend(page)
            if len(page) < CONST_FUELFINDER_PAGE_SIZE:
                break
            batch += 1
            await asyncio.sleep(REQUEST_GAP)
        return results

    async def _fetch_page(self, url: str, params: dict, retry_empty: bool) -> list[dict] | None:
        """Fetch a single page, returning None once past the last page."""
        for attempt in range(MAX_ATTEMPTS):
            token = await self._get_access_token()
            async with self._client_session.get(
                url=url.format(BASE=CONST_FUELFINDER_BASE),
                params=params,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            ) as resp:
                if resp.status == 404:
                    return None
                if resp.status == 200:
                    page = _unwrap(await resp.json(content_type=None))
                    # An empty page part way through a full pull is a transient
                    # fault on the API side, not the end of the data.
                    if page or not retry_empty:
                        return page
                elif resp.status == 401:
                    self._access_token = None
                elif resp.status == 403:
                    raise ServiceBlocked(
                        status=resp.status,
                        response=await resp.text(),
                        headers=resp.headers,
                        service=self.provider_name
                    )
                elif resp.status not in RETRYABLE_STATUS:
                    raise UpdateFailedError(
                        status=resp.status,
                        response=await resp.text(),
                        headers=resp.headers,
                        service=self.provider_name
                    )
                _LOGGER.debug("Fuel Finder request for %s returned %s, attempt %s",
                              params, resp.status, attempt + 1)
            await asyncio.sleep(2 ** attempt)
        raise UpdateFailedError(
            status=resp.status,
            response=f"Gave up after {MAX_ATTEMPTS} attempts",
            headers=resp.headers,
            service=self.provider_name
        )

    async def _get_access_token(self) -> str:
        """Return a valid access token, refreshing or regenerating as needed."""
        now = datetime.now(timezone.utc)
        if self._access_token and self._access_expires > now + TOKEN_EXPIRY_MARGIN:
            return self._access_token
        data = None
        if self._refresh_token and self._refresh_expires > now:
            data = await self._request_token(
                CONST_FUELFINDER_REFRESH,
                {
                    "client_id": self.configuration["client_id"],
                    "refresh_token": self._refresh_token
                },
                raise_on_error=False
            )
        if data is None:
            data = await self._request_token(
                CONST_FUELFINDER_TOKEN,
                {
                    "client_id": self.configuration["client_id"],
                    "client_secret": self.configuration["client_secret"]
                },
                raise_on_error=True
            )
        self._access_token = data["access_token"]
        self._access_expires = now + timedelta(seconds=int(data.get("expires_in", 3600)))
        if data.get("refresh_token"):
            self._refresh_token = data["refresh_token"]
            self._refresh_expires = now + timedelta(
                seconds=int(data.get("refresh_token_expires_in", 172800))
            )
        return self._access_token

    async def _request_token(self, url: str, payload: dict, raise_on_error: bool) -> dict | None:
        """Request an access token."""
        async with self._client_session.post(
            url=url.format(BASE=CONST_FUELFINDER_BASE),
            json=payload,
            headers={"Accept": "application/json"}
        ) as resp:
            if resp.status == 200:
                body = await resp.json(content_type=None)
                data = body.get("data", body) if isinstance(body, dict) else None
                if data and data.get("access_token"):
                    return data
            if not raise_on_error:
                _LOGGER.debug("Fuel Finder token refresh failed with %s", resp.status)
                return None
            error = ServiceBlocked if resp.status == 403 else UpdateFailedError
            raise error(
                status=resp.status,
                response=await resp.text(),
                headers=resp.headers,
                service=self.provider_name
            )

    def parse_fuels(self, fuels):
        """Not used."""
