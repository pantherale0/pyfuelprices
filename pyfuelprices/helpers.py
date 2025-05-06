"""Fuel Price helpers."""

import asyncio
import time
import math
import logging

from geopy import (
    Nominatim,
    location,
    adapters,
    exc as geopyexc
)

from ._version import __version__ as VERSION

_LOGGER = logging.getLogger(__name__)

class BoundingBox(object):
    """Represent a bounding box."""
    lat_min = None
    lon_min = None
    lat_max = None
    lon_max = None

class LeakyBucket:
    """Represent a leaky bucket algorithm rate limiter."""
    def __init__(self, max_requests, rate):
        """Create a Leaky Bucket."""
        self.capacity = max_requests
        self.rate = rate
        self.tokens = 0
        self.last_time = time.time()

    def _update_tokens(self):
        """Update tokens."""
        now = time.time()
        elapsed_time = now - self.last_time
        self.tokens = min(self.capacity, self.tokens + elapsed_time * self.rate)
        self.last_time = now

    def allow_request(self) -> bool:
        """Allow a given request."""
        self._update_tokens()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

class GeoCodeHandler:
    """Represent a geocode handler."""
    _lookup_lock: asyncio.Lock = asyncio.Lock()
    _rate_limiter: LeakyBucket = LeakyBucket(
        max_requests=1,
        rate=1
    )

    async def geocode_reverse_lookup(self, coordinates: tuple) -> location.Location:
        """Reverse GeoCode lookup."""
        async with self._lookup_lock:
            while not self._rate_limiter.allow_request():
                _LOGGER.debug("Geocoder rate limit reached (1req/s), sleeping for 1s")
                await asyncio.sleep(1)
            async with Nominatim(
                user_agent=f"pyfuelprices-{VERSION}",
                adapter_factory=adapters.AioHTTPAdapter) as geolocator:
                return await geolocator.reverse(
                    coordinates, exactly_one=True, timeout=15, addressdetails=True
                )

    def get_bounding_box(self, latitude_in_degrees, longitude_in_degrees, half_side_in_miles):
        """Return a bounding box from lat/long/radius"""
        assert half_side_in_miles > 0
        assert latitude_in_degrees >= -90.0 and latitude_in_degrees  <= 90.0
        assert longitude_in_degrees >= -180.0 and longitude_in_degrees <= 180.0

        half_side_in_km = half_side_in_miles * 1.609344
        lat = math.radians(latitude_in_degrees)
        lon = math.radians(longitude_in_degrees)

        radius  = 6371
        # Radius of the parallel at given latitude
        parallel_radius = radius*math.cos(lat)

        lat_min = lat - half_side_in_km/radius
        lat_max = lat + half_side_in_km/radius
        lon_min = lon - half_side_in_km/parallel_radius
        lon_max = lon + half_side_in_km/parallel_radius
        rad2deg = math.degrees

        box = BoundingBox()
        box.lat_min = rad2deg(lat_min)
        box.lon_min = rad2deg(lon_min)
        box.lat_max = rad2deg(lat_max)
        box.lon_max = rad2deg(lon_max)

        return box

geocoder = GeoCodeHandler()
