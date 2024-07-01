"""AUS Fuel Data Consts."""

from pyfuelprices.const import DESKTOP_USER_AGENT

FUELWATCH_API_BASE = "https://www.fuelwatch.wa.gov.au/api/"
FUELWATCH_API_PRODUCTS = f"{FUELWATCH_API_BASE}products"
FUELWATCH_API_SITES = (
    f"{FUELWATCH_API_BASE}sites"
    "?fuelType={FUELTYPE}"
)

FUELSNOOP_API_BASE = "https://jqdyvthpvgnvlojefpav.supabase.co/rest/v1/rpc/"
FUELSNOOP_API_API_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpxZH"
    "l2dGhwdmdudmxvamVmcGF2Iiwicm9sZSI6ImFu"
    "b24iLCJpYXQiOjE3MDEwODM2MzksImV4cCI6Mj"
    "AxNjY1OTYzOX0.7fEHEq5g3OFLBSyzuOObdJLZ"
    "NlqFyVJPoYre2fYzN0E"
)
FUELSNOOP_API_HEADERS = {
    "User-Agent": DESKTOP_USER_AGENT,
    "Accept": "application/json",
    "Accept-Language": "en-GB,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://www.fuelsnoop.com.au/",
    "apikey": FUELSNOOP_API_API_TOKEN,
    "authorization": f"Bearer {FUELSNOOP_API_API_TOKEN}",
    "content-profile": "public",
    "x-client-info": "supabase-ssr/0.0.10",
    "Origin": "https://www.fuelsnoop.com.au",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "Priority": "u=4",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "TE": "trailers"
}
FUELSNOOP_API_SITES = f"{FUELSNOOP_API_BASE}sites_in_view"

PETROLSPY_API_BASE = "https://petrolspy.com.au/webservice-1/"
PETROLSPY_API_HEADERS = {
    "User-Agent": DESKTOP_USER_AGENT,
    "Accept": "application/json",
    "Referer": "https://petrolspy.com.au/",
    "x-ps-fp": "06999ae0c2fa02880528b0a549374286",
    "X-Requested-With": "XMLHttpRequest"
}
PETROLSPY_API_SITES = (
    f"{PETROLSPY_API_BASE}"
    "station/box?"
    "neLat={LAT_MAX}"
    "&neLng={LNG_MAX}"
    "&swLat={LAT_MIN}"
    "&swLng={LNG_MIN}"
)
