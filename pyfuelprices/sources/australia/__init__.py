"""Australia data sources."""

from .fuelwatch import FuelWatchSource
from .fuelsnoop import FuelSnoopSource

SOURCE_MAP = {
    "fuelwatch": FuelWatchSource,
    "fuelsnoop": FuelSnoopSource
}
