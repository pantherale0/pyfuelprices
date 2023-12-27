"""Sources mapping file."""

from .netherlands import DirectLeaseTankServiceParser
from .uk.map import SOURCE_MAP as UK_SOURCE_MAP

SOURCE_MAP = {**UK_SOURCE_MAP, "directleasenl": DirectLeaseTankServiceParser}

DEFAULT_DISABLED_SOURCES = ["directleasenl"]
