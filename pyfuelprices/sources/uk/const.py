"""UK Data sources."""

CONST_PETROLPRICES_BASE = "https://mobile.app.petrolprices.com/api"
CONST_PETROLPRICES_LOGIN = "{BASE}/guest-mode/gello"
CONST_PETROLPRICES_FUELSTATIONS = "{BASE}/petrolstationsgeo/{FUEL_TYPE}/0/50/0/{RADIUS}/price?lat={LAT}&lng={LNG}"
CONST_PETROLPRICES_FUEL_MAP = {
    "1": "E5",
    "2": "E10",
    "4": "B10",
    "5": "B7"
}

CONST_FUELFINDER_BASE = "https://www.fuel-finder.service.gov.uk/api/v1"
CONST_FUELFINDER_TOKEN = "{BASE}/oauth/generate_access_token"
CONST_FUELFINDER_REFRESH = "{BASE}/oauth/regenerate_access_token"
CONST_FUELFINDER_STATIONS = "{BASE}/pfs"
CONST_FUELFINDER_PRICES = "{BASE}/pfs/fuel-prices"
CONST_FUELFINDER_PAGE_SIZE = 500
CONST_FUELFINDER_FUEL_MAP = {
    "E10": "E10",
    "E5": "E5",
    "B7_STANDARD": "B7",
    "B7_PREMIUM": "SDV",
    "B10": "B10",
    "HVO": "HVO"
}

CONST_PODPOINT_BASE = "https://mobile-api.pod-point.com/api3/v5"
CONST_PODPOINT_SEARCH = "{BASE}/addresses?payg=true&force=true&order=proximity:{LAT}:{LNG}"
CONST_PODPOINT_LOCATION = "{BASE}/addresses/{LOC_ID}/pods?include=price,model,charges,advert,unit_connectors.status,range&perpage=all&order=-availability"
