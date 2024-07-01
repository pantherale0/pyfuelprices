"""Australia data sources."""

from .fuelwatch import FuelWatchSource
from .fuelsnoop import FuelSnoopSource
from .petrolspy import PetrolSpySource

SOURCE_MAP = {
    "fuelwatch": FuelWatchSource,
    "fuelsnoop": FuelSnoopSource,
    "petrolspy": PetrolSpySource
}
