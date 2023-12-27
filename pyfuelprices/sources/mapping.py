"""Sources mapping file."""

from .uk.map import SOURCE_MAP as UK_SOURCE_MAP
from .netherlands.map import SOURCE_MAP as NL_SOURCE_MAP

SOURCE_MAP = {**UK_SOURCE_MAP, **NL_SOURCE_MAP}
COUNTRY_MAP = {
    "BE": ["directlease"],
    "NL": [k for k in NL_SOURCE_MAP],
    "UK": [k for k in UK_SOURCE_MAP]
}
