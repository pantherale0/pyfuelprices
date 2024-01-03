"""Sources mapping file."""

from .germany.tankerkoenig import TankerKoenigSource
from .uk.map import SOURCE_MAP as UK_SOURCE_MAP
from .usa.gasbuddy import GasBuddyUSASource
from .netherlands.map import SOURCE_MAP as NL_SOURCE_MAP

SOURCE_MAP = {
    **UK_SOURCE_MAP,
    **NL_SOURCE_MAP,
    "gasbuddy": GasBuddyUSASource,
    "tankerkoenig": TankerKoenigSource}
COUNTRY_MAP = {
    "BE": ["directlease"],
    "DE": ["tankerkoenig"],
    "NL": [k for k in NL_SOURCE_MAP],
    "GB": [k for k in UK_SOURCE_MAP],
    "US": ["gasbuddy"]
}
