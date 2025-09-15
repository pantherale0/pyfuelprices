"""Costco Data Source."""

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID,
    DESKTOP_USER_AGENT
)
from pyfuelprices.fuel_locations import Fuel, FuelLocation
from pyfuelprices.sources.uk import CMAParser

COSTCO_FUEL_MAPPING = {
    "5302": "E5",
    "5303": "B7",
    "5301": "E10"
}

class CostcoUKSource(CMAParser):
    """A Costco data source."""
    _url = ("https://www.costco.co.uk/rest/v2/uk/stores?fields=FULL&query=London"
            "&radius=3000000&longitude=-0.12770000100135803"
            "&latitude=51.50354766845703&returnAllStores=true&pageSize=999"
            "&lang=en_GB&curr=GBP")
    _headers = {
        "User-Agent": DESKTOP_USER_AGENT,
        "Accept": "application/json",
        "Accept-Language": "en-GB,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.costco.co.uk/store-finder?q=London"
    }
    location_cache: dict[str, FuelLocation] = {}
    provider_name: str = "costco"

    def parse_fuels(self, fuels):
        """Parse Costco Fuel."""
        parsed = []
        for fuel in fuels:
            parsed.append(Fuel(
                fuel_type=COSTCO_FUEL_MAPPING.get(fuel["name"], fuel["name"]),
                cost=float(fuel["price"])/100,
                props={}
            ))
        return parsed

    async def parse_response(self, response) -> list[FuelLocation]:
        if "stores" in response:
            response = response["stores"]
        for station in response:
            if len(station.get("gasTypes", [])) == 0:
                continue
            site_id = f"{self.provider_name}_{station['address']['id']}"
            location = FuelLocation.create(
                site_id=site_id,
                name=f"Costco {station['displayName']}",
                address=f"{station['address']['line1']}\n{station['address']['line2']}\n{station['address']['town']}\n{station['address']['postalCode']}",
                brand=self.provider_name,
                available_fuels=self.parse_fuels(
                    station["gasTypes"]
                ),
                postal_code=station["address"]["postalCode"],
                lat=station["geoPoint"]["latitude"],
                long=station["geoPoint"]["longitude"],
                currency="GBP",
                props={
                    PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                    PROP_FUEL_LOCATION_SOURCE_ID: station["address"]["id"],
                    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True
                },
                next_update=self.next_update
            )
            if site_id not in self.location_cache:
                self.location_cache[site_id] = location
            else:
                await self.location_cache[site_id].update(location)
        return list(self.location_cache.values())
