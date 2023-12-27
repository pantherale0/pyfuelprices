"""pyfuelprices locations."""

from typing import final
from datetime import datetime

from .const import CONF_FUEL_LOCATION_DYNAMIC_BUILD
from .fuel import Fuel

class FuelLocation:
    """Represents an invidual location."""

    id = ""
    name = ""
    address = ""
    lat = 0.0
    long = 0.0
    brand = ""
    available_fuels: list[Fuel] = []
    currency = ""
    last_updated: datetime | None = None
    postal_code: str | None = None
    props: dict = {}

    @final
    def __dict__(self) -> dict:
        """Convert the object to a dict."""
        fuels = {}
        for fuel in self.available_fuels:
            fuels[fuel.fuel_type] = fuel.cost
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "postal_code": self.postal_code,
            "latitude": self.lat,
            "longitude": self.long,
            "brand": self.brand,
            "available_fuels": fuels,
            "last_updated": self.last_updated,
        }

    @final
    async def update(self, updated: 'FuelLocation'):
        """Update the object."""
        self.name = updated.name
        self.address = updated.address
        self.lat = updated.lat
        self.long = updated.long
        self.brand = updated.brand
        self.last_updated = updated.last_updated
        self.postal_code = updated.postal_code
        if (
            updated.props.get(CONF_FUEL_LOCATION_DYNAMIC_BUILD, False)
            and len(self.available_fuels)>0):
            await updated.dynamic_build_fuels()
        for fuel in updated.available_fuels:
            try:
                self.get_fuel(fuel.fuel_type).update(fuel.fuel_type, fuel.cost, fuel.props)
            except ValueError:
                self.available_fuels.append(fuel)

    @final
    def get_fuel(self, f_type: str) -> Fuel:
        """Return a fuel instance."""
        for fuel in self.available_fuels:
            if fuel.fuel_type == f_type:
                return fuel
        raise ValueError(f"No existing fuel data found for {f_type}")

    @final
    async def async_get_fuel(self, f_type: str) -> Fuel:
        """Return a fuel instance."""
        if self.props.get(CONF_FUEL_LOCATION_DYNAMIC_BUILD, True):
            await self.dynamic_build_fuels()
        for fuel in self.available_fuels:
            if fuel.fuel_type == f_type:
                return fuel
        raise ValueError(f"No existing fuel data found for {f_type}")

    async def dynamic_build_fuels(self):
        """Dynamic build of fuels for when accessing this data would normally be costly."""
        if self.props.get(CONF_FUEL_LOCATION_DYNAMIC_BUILD, False):
            raise NotImplementedError("Dynamic build not available for this source.")

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
               postal_code: str | None = None
        ) -> 'FuelLocation':
        """Create an instance of fuel location."""
        location = cls()
        location.id = site_id
        location.address = address
        location.name = name
        location.lat = lat
        location.long = long
        location.brand = brand
        location.available_fuels = available_fuels
        location.last_updated = last_updated
        location.postal_code = postal_code
        return location
