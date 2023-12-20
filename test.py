
import logging
import asyncio

from pyfuelprices import FuelPrices

_LOGGER = logging.getLogger(__name__)

async def main():
    """Main init."""
    data = FuelPrices.create()
    await data.update()
    for location_id in data.find_fuel_locations_from_point(
        point=(52.570419, 1.115850),
        radius=5.0
    ):
        loc = data.get_fuel_location(location_id)
        _LOGGER.info("Found location: %s", loc.__dict__())

    _LOGGER.info("Fuels test: %s", data.find_fuel_from_point(
        point=(52.570419, 1.115850),
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
