"""Romania Fuel Sources and parsers."""

from .pecoonline import PecoOnlineSource

SOURCE_MAP = {"pecoonline": (PecoOnlineSource, 1, 1,)}
