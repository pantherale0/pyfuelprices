"""pyfuelprices locations."""

from typing import final
from datetime import datetime

from .const import PROP_FUEL_LOCATION_DYNAMIC_BUILD
from .fuel import Fuel

class FuelLocation:
    """Represents an invidual location."""

    _id = ""
    _name = ""
    _address = ""
    lat = 0.0
    long = 0.0
    _brand = ""
    available_fuels: list[Fuel] = []
    _currency = ""
    _postal_code: str | None = None
    last_updated: datetime | None = None
    next_update: datetime | None = None
    last_access: datetime | None = None
    props: dict = {}

    @final
    @property
    def id(self) -> str:
        """Return site_id."""
        self.last_access = datetime.now()
        return self._id

    @final
    @id.setter
    def id(self, new_val):
        """Set site_id"""
        self._id = new_val

    @final
    @property
    def name(self) -> str:
        """Return site name."""
        self.last_access = datetime.now()
        return self._name

    @final
    @name.setter
    def name(self, new_val):
        """Set site name."""
        self._name = new_val


    @final
    @property
    def address(self) -> str:
        """Return site address."""
        self.last_access = datetime.now()
        return self._address

    @final
    @address.setter
    def address(self, new_val):
        """Set site address."""
        self._address = new_val

    @final
    @property
    def brand(self) -> str:
        """Return fuel brand."""
        self.last_access = datetime.now()
        return self._brand

    @final
    @brand.setter
    def brand(self, new_val):
        """Set fuel brand."""
        self._brand = new_val

    @final
    @property
    def currency(self) -> str:
        """Return site name."""
        self.last_access = datetime.now()
        return self._currency

    @final
    @currency.setter
    def currency(self, new_val):
        """Set site currency."""
        self._currency = new_val

    @final
    @property
    def postal_code(self) -> str:
        """Return site postal code."""
        self.last_access = datetime.now()
        return self._postal_code

    @final
    @postal_code.setter
    def postal_code(self, new_val):
        """Set site postal code."""
        self._postal_code = new_val

    @final
    def __dict__(self) -> dict:
        """Convert the object to a dict."""
        fuels = {}
        for fuel in self.available_fuels:
            fuels[fuel.fuel_type] = fuel.cost
        return {
            "id": self._id,
            "name": self._name,
            "address": self._address,
            "postal_code": self._postal_code,
            "latitude": self.lat,
            "longitude": self.long,
            "brand": self._brand,
            "available_fuels": fuels,
            "currency": self._currency,
            "last_updated": self.last_updated.isoformat(),
            "next_update": (
                self.next_update.isoformat() if self.next_update is not None
                else "unavailable"),
            "props": self.props
        }

    @final
    async def update(self, updated: 'FuelLocation'):
        """Update the object."""
        self._name = updated.name
        self._address = updated.address
        self.lat = updated.lat
        self.long = updated.long
        self._brand = updated.brand
        self.last_updated = datetime.now()
        self._postal_code = updated.postal_code
        self.next_update = updated.next_update

        if (
            updated.props.get(PROP_FUEL_LOCATION_DYNAMIC_BUILD, False)
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
        if self.props.get(PROP_FUEL_LOCATION_DYNAMIC_BUILD, False):
            await self.dynamic_build_fuels()
        for fuel in self.available_fuels:
            if fuel.fuel_type == f_type:
                return fuel
        raise ValueError(f"No existing fuel data found for {f_type}")

    async def dynamic_build_fuels(self):
        """Dynamic build of fuels for when accessing this data would normally be costly."""
        return True

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
               next_update: datetime = None,
               postal_code: str | None = None,
               currency: str = "",
               props: dict = None
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
        location.next_update = next_update
        return location
