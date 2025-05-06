"""Austria consts."""

CONST_API_BASE = "https://www.spritpreisrechner.at/api"
CONST_API_SEARCH_REGIONS = (
    f"{CONST_API_BASE}/search/gas-stations/by-region?"
    "code={REG_CODE}&fuelType={FUEL_TYPE}&includeClosed=true&type={REG_TYPE}"
)
CONST_API_SEARCH_ADDRESS = (
    f"{CONST_API_BASE}/search/gas-stations/by-address?"
    "latitude={LAT}&longitude={LONG}&fuelType={FUEL_TYPE}&includeClosed=true"
)
CONST_API_GET_REGIONS = f"{CONST_API_BASE}/regions"
CONST_FUELS = ["DIE", "SUP", "GAS"]