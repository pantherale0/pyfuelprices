"""pyfuelprices schema storage."""

import voluptuous as vol

from .const import PROP_AREA_LONG, PROP_AREA_LAT, PROP_AREA_RADIUS

SOURCE_BASE_CONFIG = vol.Schema({}, extra=vol.ALLOW_EXTRA)
AREA_CONFIG = vol.Schema({
    vol.Inclusive(PROP_AREA_LAT, "loc"): float,
    vol.Inclusive(PROP_AREA_LONG, "loc"): float,
    vol.Inclusive(PROP_AREA_RADIUS, "loc"): float
})

BASE_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional("global"): SOURCE_BASE_CONFIG,
        vol.Required("providers",default={}): SOURCE_BASE_CONFIG,
        vol.Required("areas", default=[]): list[AREA_CONFIG],
        vol.Optional("country_code", default=""): str,
        vol.Required("update_interval", default=24): vol.Any(float, int),
        vol.Required("timeout", default=30): vol.Any(float, int)
    },
    extra=vol.ALLOW_EXTRA
)
