"""Sources mapping file."""

from .argentina import SOURCE_MAP as AR_SOURCE_MAP
from .austria import SOURCE_MAP as AT_SOURCE_MAP
from .australia import SOURCE_MAP as AU_SOURCE_MAP
from .belgium import SOURCE_MAP as BE_SOURCE_MAP
from .brazil import SOURCE_MAP as BR_SOURCE_MAP
from .canada import SOURCE_MAP as CA_SOURCE_MAP
from .germany import SOURCE_MAP as DE_SOURCE_MAP
from .greece import SOURCE_MAP as GR_SOURCE_MAP
from .romania import SOURCE_MAP as RO_SOURCE_MAP
from .uk.map import SOURCE_MAP as UK_SOURCE_MAP
from .usa import SOURCE_MAP as US_SOURCE_MAP
from .netherlands import SOURCE_MAP as NL_SOURCE_MAP
from .new_zealand import SOURCE_MAP as NZ_SOURCE_MAP
from .slovenia import SOURCE_MAP as SI_SOURCE_MAP
from .switzerland import SOURCE_MAP as CH_SOURCE_MAP

# Fields are as follows:
# Key - Provider Name
# Value - (Provider Class, Enabled, Available, Country Mapping Enabled)
# Available field is used to control what options are
# shown in the Home Assistant config wizard.
# The last int is an optional value that defines if the provider will be
# included in the area auto mapping system, if set to 0, the provider
# can only be configured manually

SOURCE_MAP: dict[str, tuple[object, int, int]] = {
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
    **SI_SOURCE_MAP,
    **BE_SOURCE_MAP,
    **CA_SOURCE_MAP,
    **NZ_SOURCE_MAP
}

FULL_COUNTRY_MAP = {
    "AR": [k for k in AR_SOURCE_MAP],
    "BE": [k for k in BE_SOURCE_MAP],
    "BR": [k for k in BR_SOURCE_MAP],
    "CA": [k for k in CA_SOURCE_MAP],
    "DE": [k for k in DE_SOURCE_MAP],
    "NL": [k for k in NL_SOURCE_MAP],
    "NZ": [k for k in NZ_SOURCE_MAP],
    "GB": [k for k in UK_SOURCE_MAP],
    "US": [k for k in US_SOURCE_MAP],
    "AU": [k for k in AU_SOURCE_MAP],
    "AT": [k for k in AT_SOURCE_MAP],
    "CH": [k for k in CH_SOURCE_MAP],
    "RO": [k for k in RO_SOURCE_MAP],
    "GR": [k for k in GR_SOURCE_MAP],
    "SI": [k for k in SI_SOURCE_MAP]
}

COUNTRY_MAP = {
    "AR": [k for k, v in AR_SOURCE_MAP.items() if len(v)==3 and v[1]==1],
    "BE": [k for k, v in BE_SOURCE_MAP.items() if len(v)==3 and v[1]==1],
    "BR": [k for k, v in BR_SOURCE_MAP.items() if len(v)==3 and v[1]==1],
    "CA": [k for k, v in CA_SOURCE_MAP.items() if len(v)==3 and v[1]==1],
    "DE": [k for k, v in DE_SOURCE_MAP.items() if len(v)==3 and v[1]==1],
    "NL": [k for k, v in NL_SOURCE_MAP.items() if len(v)==3 and v[1]==1],
    "NZ": [k for k, v in NZ_SOURCE_MAP.items() if len(v)==3 and v[1]==1],
    "GB": [k for k, v in UK_SOURCE_MAP.items() if len(v)==3 and v[1]==1],
    "US": [k for k, v in US_SOURCE_MAP.items() if len(v)==3 and v[1]==1],
    "AU": [k for k, v in AU_SOURCE_MAP.items() if len(v)==3 and v[1]==1],
    "AT": [k for k, v in AT_SOURCE_MAP.items() if len(v)==3 and v[1]==1],
    "CH": [k for k, v in CH_SOURCE_MAP.items() if len(v)==3 and v[1]==1],
    "RO": [k for k, v in RO_SOURCE_MAP.items() if len(v)==3 and v[1]==1],
    "GR": [k for k, v in GR_SOURCE_MAP.items() if len(v)==3 and v[1]==1],
    "SI": [k for k, v in SI_SOURCE_MAP.items() if len(v)==3 and v[1]==1]
}
