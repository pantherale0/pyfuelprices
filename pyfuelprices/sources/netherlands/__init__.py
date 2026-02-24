"""Netherlands Fuel Sources and parsers."""

from .directlease import DirectLeaseTankServiceParser
from .anwbonderweg import ANWBOnderwegDataSource

SOURCE_MAP = {"directlease": (DirectLeaseTankServiceParser, 1, 1, 0),
              "anwbonderweg":(ANWBOnderwegDataSource, 1, 1, 0, 0)}
