"""Sources mapping file."""

from .argentina import SOURCE_MAP as AR_SOURCE_MAP
from .austria import SOURCE_MAP as AT_SOURCE_MAP
from .australia import SOURCE_MAP as AU_SOURCE_MAP
from .brazil import SOURCE_MAP as BR_SOURCE_MAP
from .germany import SOURCE_MAP as DE_SOURCE_MAP
from .greece import SOURCE_MAP as GR_SOURCE_MAP
from .romania import SOURCE_MAP as RO_SOURCE_MAP
from .uk.map import SOURCE_MAP as UK_SOURCE_MAP
from .usa import SOURCE_MAP as US_SOURCE_MAP
from .netherlands import SOURCE_MAP as NL_SOURCE_MAP
from .slovenia import SOURCE_MAP as SI_SOURCE_MAP
from .switzerland import SOURCE_MAP as CH_SOURCE_MAP

SOURCE_MAP = {
    **UK_SOURCE_MAP,
    **NL_SOURCE_MAP,
    **US_SOURCE_MAP,
    **DE_SOURCE_MAP,
    **AT_SOURCE_MAP,
    **AU_SOURCE_MAP,
    **CH_SOURCE_MAP,
    **RO_SOURCE_MAP,
    **GR_SOURCE_MAP,
    **BR_SOURCE_MAP,
    **AR_SOURCE_MAP,
    **SI_SOURCE_MAP
}

COUNTRY_MAP = {
    "AR": [k for k in AR_SOURCE_MAP],
    "BE": ["directlease"],
    "BR": [k for k in BR_SOURCE_MAP],
    "CA": ["gasbuddy"],
    "DE": [k for k in DE_SOURCE_MAP],
    "NL": [k for k in NL_SOURCE_MAP],
    "NZ": ["petrolspy"],
    "GB": [k for k in UK_SOURCE_MAP],
    "US": [k for k in US_SOURCE_MAP],
    "AU": [k for k in AU_SOURCE_MAP],
    "AT": [k for k in AT_SOURCE_MAP],
    "CH": [k for k in CH_SOURCE_MAP],
    "RO": [k for k in RO_SOURCE_MAP],
    "GR": [k for k in GR_SOURCE_MAP],
    "SI": [k for k in SI_SOURCE_MAP]
}
