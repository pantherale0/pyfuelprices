"""pyfuelprices schema storage."""

import voluptuous as vol

BASE_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional("global"): {}
    },
    extra=vol.ALLOW_EXTRA
)

SOURCE_BASE_CONFIG = vol.Schema({}, extra=vol.ALLOW_EXTRA)
