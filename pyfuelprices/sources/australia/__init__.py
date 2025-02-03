"""Australia data sources."""

from .fuelwatch import FuelWatchSource
from .fuelsnoop import FuelSnoopSource
from .petrolspy import PetrolSpySource

SOURCE_MAP = {
    "fuelwatch": (FuelWatchSource, 1, 1,),
    "fuelsnoop": (FuelSnoopSource, 1, 1,),
    "petrolspy": (PetrolSpySource, 1, 1,)
}
