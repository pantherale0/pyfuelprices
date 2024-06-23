"""Netherlands data const."""

API_BASE = "https://pg-app-hnf14cfy2xb2v9x9eueuchcd2xyetd.scalabl.cloud"

PECO_ONLINE_API = f"{API_BASE}/1/classes/farapret3"
PECO_APP_ID = "YueWcf0orjSz3IQmaT8yBNDTM5POP0mOU6EDyE3U"
PECO_APP_CLIENT_KEY = "ctPx9Ahrz9aaXhEvN0oWCzlX8FHX1cv3r7vZwxH8"

USER_AGENT = "Parse Android SDK API Level 34"
X_PARSE_OS_VERSION = "14"
X_PARSE_APP_DISPLAY_VERSION = "4.0"
X_PARSE_APP_BUILD_VERSION = "69"

PECO_STANDARD_HEADERS = {
    "X-Parse-Application-Id": PECO_APP_ID,
    "X-Parse-App-Build-Version": X_PARSE_APP_BUILD_VERSION,
    "X-Parse-App-Display-Version": X_PARSE_APP_DISPLAY_VERSION,
    "X-Parse-OS-Version": X_PARSE_OS_VERSION,
    "User-Agent": USER_AGENT,
    "X-Parse-Installation-Id": None,
    "X-Parse-Client-Key": PECO_APP_CLIENT_KEY,
    "Content-Type": "application/json"
}

PECO_QUERY_CLAUSE = '{\"Benzina_Regular\":{\"$gt\":0},\"DoarGPL\":{\"$ne\":1},\"Retea\":{\"$in\":[\"Gazprom\",\"Lukoil\",\"Mol\",\"OMV\",\"Petrom\",\"Rompetrol\",\"Socar\",\"BLKOil\",\"Ozana\",\"RST\"]}}'

PECO_FUEL_MAPPING = {
    "Benzina_Regular": "Gasoline Regular",
    "Benzina_Premium": "Gasoline Premium",
    "Motorina_Regular": "Diesel Regular",
    "Motorina_Premium": "Diesel Premium",
    "GPL": "GPL",
    "AdBlue": "AdBlue"
}
