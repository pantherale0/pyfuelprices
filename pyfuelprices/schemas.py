"""pyfuelprices schema storage."""

import voluptuous as vol

SOURCE_BASE_CONFIG = vol.Schema({}, extra=vol.ALLOW_EXTRA)
AREA_CONFIG = vol.Schema({
    vol.All()
})

BASE_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional("global"): SOURCE_BASE_CONFIG,
        vol.Required("providers",default={}): SOURCE_BASE_CONFIG,
        vol.Required("areas", default=[]): list,
        vol.Optional("country_code", default=""): str,
        vol.Required("update_interval", default=24): int,
        vol.Required("timeout", default=30): int
    },
    extra=vol.ALLOW_EXTRA
)
