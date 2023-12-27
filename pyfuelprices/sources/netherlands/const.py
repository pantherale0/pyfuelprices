"""Netherlands data const."""

API_BASE = "https://tankservice.app-it-up.com/Tankservice/v2"

DIRECTLEASE_API_PLACES = f"{API_BASE}/places?fmt=web&country=NL&country=BE&lang=en"
DIRECTLEASE_API_STATION = API_BASE + "/places/{station_id}?_v48&lang=en"
