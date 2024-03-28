
import logging
import asyncio

from datetime import timedelta

from pyfuelprices import FuelPrices
from pyfuelprices.const import PROP_AREA_LAT, PROP_AREA_LONG, PROP_AREA_RADIUS

_LOGGER = logging.getLogger(__name__)

async def main():
    """Main init."""
    data = FuelPrices.create(
        enabled_sources=["comparis"],
        configured_areas=[
            {
                PROP_AREA_RADIUS: 5.0,
                PROP_AREA_LAT: 47.042277,
                PROP_AREA_LONG: 9.068475
            }
        ],
        update_interval=timedelta(minutes=2)
    )
    while True:
        await data.update()
        # for loc in await data.find_fuel_locations_from_point(
        #     coordinates=(52.570419, 1.115850),
        #     radius=25.0
        # ):
        #     _LOGGER.info("Found location: %s", loc)

        _LOGGER.info("Comparis CH test...")
        for loc in await data.find_fuel_locations_from_point(
            coordinates=(47.042277, 9.068475),
            radius=5.0
        ):
            _LOGGER.info("Found location: %s", loc)

        # _LOGGER.info("FuelWatch AU test...")
        # for loc in await data.find_fuel_locations_from_point(
        #     coordinates=(-31.99432700, 115.93068100),
        #     radius=5.0
        # ):
        #     _LOGGER.info("Found location: %s", loc)

        # _LOGGER.info("DirectLease NL test...")
        # for loc in await data.find_fuel_locations_from_point(
        #     coordinates=(52.23817, 6.58763),
        #     radius=5.0
        # ):
        #     _LOGGER.info("Found location: %s", loc)

        # _LOGGER.info("Fuels test (DirectLease): %s", await data.find_fuel_from_point(
        #     coordinates=(52.23817, 6.58763),
        #     radius=5.0,
        #     fuel_type="B7"
        # ))


        # _LOGGER.info("Austria test...")
        # for loc in await data.find_fuel_locations_from_point(
        #     coordinates=(48.5140105, 14.5043854),
        #     radius=25.0,
        # ):
        #     _LOGGER.info("Found location: %s", loc)

        # _LOGGER.info("GasBuddy USA Test...")
        # for loc in await data.find_fuel_locations_from_point(
        #     coordinates=(38.906316, -77.054750),
        #     radius=5.0
        # ):
        #     _LOGGER.info("Found location: %s", loc)

        # if "gasbuddy" in data.configured_sources:
        #     _LOGGER.info("GasBuddy retrieve individual station test: %s",
        #                 await data.configured_sources["gasbuddy"].get_site(916))

        # _LOGGER.info("Fuels test: %s", await data.find_fuel_from_point(
        #     coordinates=(52.570419, 1.115850),
        #     radius=25.0,
        #     fuel_type="B7"
        # ))

        await asyncio.sleep(15)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
