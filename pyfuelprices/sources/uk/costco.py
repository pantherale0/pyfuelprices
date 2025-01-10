"""Costco Data Source."""

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID,
    DESKTOP_USER_AGENT
)
from pyfuelprices.fuel_locations import Fuel, FuelLocation
from pyfuelprices.sources import Source

COSTCO_FUEL_MAPPING = {
    "Premium Unleaded Petrol": "E5",
    "Premium Diesel": "B7",
    "Unleaded Petrol": "E10"
}

class CostcoUKSource(Source):
    """A Costco data source."""
    _url = "https://www.costco.co.uk/store-finder/search?q=United%20Kingdom&page=0"
    _headers = {
        "User-Agent": DESKTOP_USER_AGENT,
        "Accept": "application/json",
        "Accept-Language": "en-GB,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.costco.co.uk/store-finder"
    }
    location_cache: dict[str, FuelLocation] = {}
    provider_name: str = "costco"

    def parse_fuels(self, fuels):
        """Parse Costco Fuel."""
        parsed = []
        for service in fuels:
            if service["code"] == "GAS_STATION":
                fuels = service["gasTypes"]
                break
        for fuel in fuels:
            parsed.append(Fuel(
                fuel_type=COSTCO_FUEL_MAPPING.get(fuel["name"], fuel["name"]),
                cost=float(fuel["price"])/100,
                props={}
            ))
        return parsed

    async def parse_response(self, response) -> list[FuelLocation]:
        if "data" in response:
            response = response["data"]
        for station in response:
            if "Petrol Station" not in station["features"]:
                continue
            site_id = f"{self.provider_name}_{station['addressId']}"
            location = FuelLocation.create(
                site_id=site_id,
                name=f"Costco {station["displayName"]}",
                address=f"{station["line1"]}\n{station["line2"]}\n{station["town"]}\n{station["postalCode"]}",
                brand=self.provider_name,
                available_fuels=self.parse_fuels(
                    station["availableServices"]
                ),
                postal_code=station["postalCode"],
                lat=station["latitude"],
                long=station["longitude"],
                currency="GBP",
                props={
                    PROP_FUEL_LOCATION_SOURCE: self.provider_name,
                    PROP_FUEL_LOCATION_SOURCE_ID: station['addressId'],
                    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True
                },
                next_update=self.next_update
            )
            if site_id not in self.location_cache:
                self.location_cache[site_id] = location
            else:
                await self.location_cache[site_id].update(location)
        return list(self.location_cache.values())
