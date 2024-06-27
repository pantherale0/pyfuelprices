"""Fuel Price helpers."""

import math

from geopy import (
    Nominatim,
    location,
    adapters
)

from ._version import __version__ as VERSION

async def geocode_reverse_lookup(coordinates: tuple) -> location.Location:
    """Reverse GeoCode lookup."""
    async with Nominatim(
        user_agent=f"pyfuelprices-{VERSION}",
        adapter_factory=adapters.AioHTTPAdapter) as geolocator:
        return await geolocator.reverse(coordinates, exactly_one=True, timeout=15, addressdetails=True)

class BoundingBox(object):
    """Represent a bounding box."""
    lat_min = None
    lon_min = None
    lat_max = None
    lon_max = None

def get_bounding_box(latitude_in_degrees, longitude_in_degrees, half_side_in_miles):
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
