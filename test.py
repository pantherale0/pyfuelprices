
import logging
import asyncio

from datetime import timedelta

from pyfuelprices import FuelPrices
from pyfuelprices.const import PROP_AREA_LAT, PROP_AREA_LONG, PROP_AREA_RADIUS

_LOGGER = logging.getLogger(__name__)

async def main():
    """Main init."""
    data = FuelPrices.create(
        enabled_sources=["petrolspy"],
        configured_areas=[
            {
                PROP_AREA_RADIUS: 5.0,
                PROP_AREA_LAT: 52.23817,
                PROP_AREA_LONG: 6.58763
            },
            {
                PROP_AREA_LAT: 38.906316,
                PROP_AREA_LONG: -77.054750,
                PROP_AREA_RADIUS: 5.0 # US (No locality)
            },
            {
                PROP_AREA_LAT: 40.157349,
                PROP_AREA_LONG: -75.217079,
                PROP_AREA_RADIUS: 5.0 # US (With locality)
            },
            {
                PROP_AREA_LAT: 53.068464,
                PROP_AREA_LONG: 12.532709,
                PROP_AREA_RADIUS: 5.0
            },
            {
                PROP_AREA_LAT: -31.99432700,
                PROP_AREA_LONG: 115.93068100,
                PROP_AREA_RADIUS: 5.0
            },
            {
                PROP_AREA_LAT: 48.5140105,
                PROP_AREA_LONG: 14.5043854,
                PROP_AREA_RADIUS: 25.0 # austria
            },
            {
                PROP_AREA_LAT: 39.2062720,
                PROP_AREA_LONG: 22.2513570,
                PROP_AREA_RADIUS: 5.0 # Greece
            },
            {
                PROP_AREA_LAT: -27.470750,
                PROP_AREA_LONG: 153.036804,
                PROP_AREA_RADIUS: 15.0 # AUS (FuelSnoop)
            },
            {
                PROP_AREA_LAT: -36.975624329980654,
                PROP_AREA_LONG: 174.78417701477935,
                PROP_AREA_RADIUS: 15.0 # NZ (PetrolSpy)
            }
        ],
        update_interval=timedelta(minutes=5)
    )
    while True:
        await data.update()
        # for loc in await data.find_fuel_locations_from_point(
        #     coordinates=(52.570419, 1.115850),
        #     radius=25.0
        # ):
        #     _LOGGER.info("Found location: %s", loc)

        # _LOGGER.info("TankerKoenig DE test...")
        # for loc in await data.find_fuel_locations_from_point(
        #     coordinates=(53.068464, 12.532709),
        #     radius=5.0
        # ):
        #     _LOGGER.info("Found location: %s", loc)

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
        # )) #UK

        # _LOGGER.info("Fuels test: %s", await data.find_fuel_from_point(
        #     coordinates=(39.2062720, 22.2513570),
        #     radius=30.0,
        #     fuel_type="95"
        # )) #GR

        _LOGGER.info("Fuels test: %s", await data.find_fuel_from_point(
            coordinates=(-27.470750, 153.036804),
            radius=20.0,
            fuel_type="DSL"
        )) #AUS (FuelSnoop)

        await asyncio.sleep(15)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
