"""Brazil sources."""

from .gaspass import GasPassSource

SOURCE_MAP = {
    "gaspass": (GasPassSource, 1, 1,)
}
