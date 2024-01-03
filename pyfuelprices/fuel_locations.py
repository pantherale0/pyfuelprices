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
    _lat = 0.0
    _long = 0.0
    _brand = ""
    _available_fuels: list[Fuel] = []
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
    def lat(self) -> float:
        """Return site latitude."""
        self.last_access = datetime.now()
        return self._lat

    @final
    @lat.setter
    def lat(self, new_val):
        """Set site lat"""
        self._lat = new_val

    @final
    @property
    def long(self) -> float:
        """Return site longitude."""
        self.last_access = datetime.now()
        return self._long

    @final
    @long.setter
    def long(self, new_val):
        """Set site longitude."""
        self._long = new_val

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
    def available_fuels(self) -> list[Fuel]:
        """Return site name."""
        self.last_access = datetime.now()
        return self._available_fuels

    @final
    @available_fuels.setter
    def available_fuels(self, new_val):
        """Set available fuels."""
        self._available_fuels = new_val

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
        for fuel in self._available_fuels:
            fuels[fuel.fuel_type] = fuel.cost
        return {
            "id": self._id,
            "name": self._name,
            "address": self._address,
            "postal_code": self._postal_code,
            "latitude": self._lat,
            "longitude": self._long,
            "brand": self._brand,
            "available_fuels": fuels,
            "currency": self._currency,
            "last_updated": self.last_updated.isoformat(),
            "next_update": (
                self.next_update.isoformat() if self.next_update is not None
                else "unavailable"),
        }

    @final
    async def update(self, updated: 'FuelLocation'):
        """Update the object."""
        self._name = updated.name
        self._address = updated.address
        self._lat = updated.lat
        self._long = updated.long
        self._brand = updated.brand
        self.last_updated = updated.last_updated
        self._postal_code = updated.postal_code
        if (
            updated.props.get(PROP_FUEL_LOCATION_DYNAMIC_BUILD, False)
            and len(self._available_fuels)>0):
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
        if self.props.get(PROP_FUEL_LOCATION_DYNAMIC_BUILD, False):
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
               postal_code: str | None = None,
               currency: str = "",
               props: dict = None
        ) -> 'FuelLocation':
        """Create an instance of fuel location."""
        location = cls()
        location._id = site_id
        location._address = address
        location._name = name
        location._lat = lat
        location._long = long
        location._brand = brand
        location._available_fuels = available_fuels
        location._postal_code = postal_code
        location._currency = currency
        location.last_updated = last_updated
        location.props = props
        return location
