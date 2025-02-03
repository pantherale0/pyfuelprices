"""Netherlands Fuel Sources and parsers."""

from .directlease import DirectLeaseTankServiceParser

SOURCE_MAP = {"directlease": (DirectLeaseTankServiceParser, 1, 1, 0)}
