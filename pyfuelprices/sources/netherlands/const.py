"""Netherlands data const."""

API_BASE = "https://tankservice.app-it-up.com/Tankservice/v2"

DIRECTLEASE_API_PLACES = f"{API_BASE}/places?fmt=web&country=NL&country=BE&lang=en"
DIRECTLEASE_API_STATION = API_BASE + "/places/{station_id}?_v48&lang=en"

ANWB_API_BASE = "https://api.anwb.nl/routing/points-of-interest/v3/all?type-filter=FUEL_STATION"

"""ANWB uses bounding box, this bounding box covers most of the Netherlands"""

ANWB_API_FUEL_STATION= f"{ANWB_API_BASE}&bounding-box-filter=51.910799185914925%2C3.956571023413062%2C53.10710621927336%2C8.353868854217268"
