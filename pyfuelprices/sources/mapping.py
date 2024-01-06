"""Sources mapping file."""

from .austria import SOURCE_MAP as AT_SOURCE_MAP
from .australia import SOURCE_MAP as AU_SOURCE_MAP
from .germany import SOURCE_MAP as DE_SOURCE_MAP
from .uk.map import SOURCE_MAP as UK_SOURCE_MAP
from .usa import SOURCE_MAP as US_SOURCE_MAP
from .netherlands import SOURCE_MAP as NL_SOURCE_MAP

SOURCE_MAP = {
    **UK_SOURCE_MAP,
    **NL_SOURCE_MAP,
    **US_SOURCE_MAP,
    **DE_SOURCE_MAP,
    **AT_SOURCE_MAP,
    **AU_SOURCE_MAP
}

COUNTRY_MAP = {
    "BE": ["directlease"],
    "DE": [k for k in DE_SOURCE_MAP],
    "NL": [k for k in NL_SOURCE_MAP],
    "GB": [k for k in UK_SOURCE_MAP],
    "US": [k for k in US_SOURCE_MAP],
    "AU": [k for k in AU_SOURCE_MAP],
    "AT": [k for k in AT_SOURCE_MAP]
}
