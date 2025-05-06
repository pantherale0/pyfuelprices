"""Germany consts."""

CONST_TANKERKOENIG_API_BASE = "https://tankerkoenig.de/ajax_v3_public/"
CONST_TANKERKOENIG_GET_STATIONS = (
    f"{CONST_TANKERKOENIG_API_BASE}get_stations_near_postcode.php"
    "?postcode={POSTCODE}&radius={RADIUS}"
)
