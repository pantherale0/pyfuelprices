"""USA Gas price data source."""

from .gasbuddy import GasBuddyUSASource

SOURCE_MAP = {
    "gasbuddy": GasBuddyUSASource
}
