"""Greece data const."""

FUELGR_API_DEV = "android.4.0-b2da2cf97330ca3b"
FUELGR_API_SIG = "google/coral/coral:14/UQ1A.240205.004/1709778835:userdebug/release-keys"
FUELGR_API_APKSIG = "UPJ2YQunu9eGXu8a/WOiVNAZlYA="

FUELGR_GET_DATA = (
    "https://deixto.gr/fuel/get_data_v4.php?"
    f"dev={FUELGR_API_DEV}"
    "&lat={LAT}"
    "&long={LONG}"
    "&f={FUEL}"
    "&b={BRAND}"
    "&d=30"
    "&p={QUALITY}"
    f"&dSig={FUELGR_API_SIG}"
    "&iLoc=unknown"
    f"&apkSig={FUELGR_API_APKSIG}"
)
FUELGR_GET_STATION_PRICES = (
    "https://deixto.gr/fuel/get_gasstation_prices.php?"
    f"dev={FUELGR_API_DEV}"
    "&gsid={ID}"
)

FUELGR_FUEL_TYPE_MAPPING = {
    "1": "95",
    "2": "98-100",
    "3": "Super",
    "4": "Diesel",
    "5": "Heating Diesel",
    "6": "LPG",
    "7": "Home Heating Diesel",
    "8": "CNG"
}

FUELGR_BRAND_MAPPING = {
    "0": "ALL",
    "1": "ΑΝΕΞΑΡΤΗΤΟ ΠΡΑΤΗΡΙΟ",
    "2": "JETOIL",
    "3": "SHELL",
    "5": "ETEKA",
    "6": "AVIN",
    "8": "EKO",
    "9": "REVOIL",
    "10": "BP",
    "11": "ΕΛΙΝΟΙΛ",
    "13": "CYCLON",
    "17": "KAOIL"
}
