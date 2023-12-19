"""pyfuelprices locations."""

from datetime import datetime

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
    last_updated: datetime | None = None

    def update(self, updated: 'FuelLocation'):
        """Update the object."""
        self.name = updated.name
        self.address = updated.address
        self.lat = updated.lat
        self.long = updated.long
        self.brand = updated.brand
        for fuel in updated.available_fuels:
            try:
                self.get_fuel(fuel.fuel_type).update(fuel.fuel_type, fuel.cost, fuel.props)
            except ValueError:
                self.available_fuels.append(fuel)

    def get_fuel(self, f_type: str) -> Fuel:
        """Return a fuel instance."""
        for fuel in self.available_fuels:
            if fuel.fuel_type == f_type:
                return fuel
        raise ValueError(f"No existing fuel data found for {f_type}")

    @classmethod
    def create(cls,
               name: str,
               address: str,
               lat: float,
               long: float,
               brand: str,
               available_fuels
        ) -> 'FuelLocation':
        """Create an instance of fuel location."""
        location = cls()
        location.address = address
        location.name = name
        location.lat = lat
        location.long = long
        location.brand = brand
        location.available_fuels = available_fuels
