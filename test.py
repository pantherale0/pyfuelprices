
import logging
import asyncio

from pyfuelprices import FuelPrices
from pyfuelprices.const import PROP_AREA_LAT, PROP_AREA_LONG, PROP_AREA_RADIUS

_LOGGER = logging.getLogger(__name__)

async def main():
    """Main init."""
    data = FuelPrices.create(
        country_code="US",
        configured_areas=[
            {
                PROP_AREA_RADIUS: 5.0,
                PROP_AREA_LAT: 52.23817,
                PROP_AREA_LONG: 6.58763
            },
            {
                PROP_AREA_LAT: 38.906316,
                PROP_AREA_LONG: -77.054750,
                PROP_AREA_RADIUS: 5.0
            }
        ]
    )
    await data.update()
    for loc in await data.find_fuel_locations_from_point(
        coordinates=(52.570419, 1.115850),
        radius=5.0
    ):
        _LOGGER.info("Found location: %s", loc.__dict__())

    _LOGGER.info("DirectLease NL test...")
    for loc in await data.find_fuel_locations_from_point(
        coordinates=(52.23817, 6.58763),
        radius=5.0
    ):
        _LOGGER.info("Found location: %s", loc.__dict__())

    _LOGGER.info("Fuels test (DirectLease): %s", await data.find_fuel_from_point(
        coordinates=(52.23817, 6.58763),
        radius=5.0,
        fuel_type="B7"
    ))

    _LOGGER.info("GasBuddy USA Test...")
    for loc in await data.find_fuel_locations_from_point(
        coordinates=(38.906316, -77.054750),
        radius=5.0
    ):
        _LOGGER.info("Found location: %s", loc.__dict__())

    _LOGGER.info("GasBuddy retrieve individual station test: %s",
                 await data.configured_sources["gasbuddy"].get_site(916))

    _LOGGER.info("Fuels test: %s", await data.find_fuel_from_point(
        coordinates=(52.570419, 1.115850),
        radius=25.0,
        fuel_type="B7"
    ))

    await asyncio.sleep(15)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
