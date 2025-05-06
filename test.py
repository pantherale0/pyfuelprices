
import logging
import asyncio
import os

from dotenv import load_dotenv

import voluptuous as vol

from pyfuelprices import FuelPrices, SOURCE_MAP
from pyfuelprices.const import PROP_AREA_LAT, PROP_AREA_LONG, PROP_AREA_RADIUS

load_dotenv(".env_config")

_LOGGER = logging.getLogger(__name__)

async def main():
    """Main init."""
    enabled_sources=["finelly"]
    configs = {
        "providers": {},
        "areas": [
            {
                PROP_AREA_RADIUS: 5.0,
                PROP_AREA_LAT: 52.041627,
                PROP_AREA_LONG: -0.759651 # UK
            },
            {
                PROP_AREA_RADIUS: 5.0,
                PROP_AREA_LAT: 52.23817,
                PROP_AREA_LONG: 6.58763 # Netherlands
            },
            {
                PROP_AREA_LAT: 49.134068,
                PROP_AREA_LONG: -122.889980,
                PROP_AREA_RADIUS: 5.0
            }, # CA
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
                PROP_AREA_LAT: 48.212120650046984,
                PROP_AREA_LONG: 14.287071446311938,
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
                PROP_AREA_LAT: -36.789642,
                PROP_AREA_LONG: 174.728652,
                PROP_AREA_RADIUS: 15.0 # NZ (PetrolSpy)
            },
            {
                PROP_AREA_LAT: 46.945200,
                PROP_AREA_LONG: 7.464844,
                PROP_AREA_RADIUS: 15.0 # CH
            },
            {
                PROP_AREA_LAT: -23.5557714,
                PROP_AREA_LONG: -46.6395571,
                PROP_AREA_RADIUS: 25.0 # Brazil
            },
            {
                PROP_AREA_LAT: -34.658476,
                PROP_AREA_LONG: -58.529443,
                PROP_AREA_RADIUS: 25.0 # Argentina
            },
            {
                PROP_AREA_LAT: 46.053478,
                PROP_AREA_LONG: 14.510424,
                PROP_AREA_RADIUS: 25.0 # Slovenia
            },
        ],
        "country_code": ""
    }
    for src in enabled_sources:
        if src in SOURCE_MAP:
            configs["providers"].setdefault(src, {})
            if FuelPrices.source_requires_config(src):
                schema: vol.Schema = SOURCE_MAP[src][0].attr_config
                for attr in schema.schema:
                    env_name = f"{src.upper()}_{str(attr).upper()}"
                    env = os.environ.get(env_name)
                    configs["providers"][src][str(attr)] = env or input("Enter a value for " + str(attr) + ": ")
            else:
                configs["providers"][src]

    data = FuelPrices.create(configuration=configs)
    while True:
        try:
            await data.update()
        except Exception as exc:
            pass
        for loc in await data.find_fuel_locations_from_point(
            coordinates=(52.040616, -0.768702),
            radius=5.0
        ):
            _LOGGER.info("Found location: %s", loc)

        _LOGGER.info("Comparis CH test...")
        for loc in await data.find_fuel_locations_from_point(
            coordinates=(47.042277, 9.068475),
            radius=5.0
        ):
            _LOGGER.info("Found location: %s", loc)

        _LOGGER.info("FuelWatch AU test...")
        for loc in await data.find_fuel_locations_from_point(
            coordinates=(-31.99432700, 115.93068100),
            radius=5.0
        ):
            _LOGGER.info("Found location: %s", loc)

        _LOGGER.info("DirectLease NL test...")
        for loc in await data.find_fuel_locations_from_point(
            coordinates=(52.23817, 6.58763),
            radius=5.0
        ):
            _LOGGER.info("Found location: %s", loc)

        _LOGGER.info("Fuels test (DirectLease): %s", await data.find_fuel_from_point(
            coordinates=(52.23817, 6.58763),
            radius=5.0,
            fuel_type="B7"
        ))


        _LOGGER.info("Austria test...")
        for loc in await data.find_fuel_locations_from_point(
            coordinates=(48.212120650046984, 14.287071446311938),
            radius=25.0,
        ):
            _LOGGER.info("Found location: %s", loc)

        _LOGGER.info("GasBuddy USA Test...")
        for loc in await data.find_fuel_locations_from_point(
            coordinates=(38.906316, -77.054750),
            radius=5.0
        ):
            _LOGGER.info("Found location: %s", loc)

        if "gasbuddy" in data.configured_sources:
            _LOGGER.info("GasBuddy retrieve individual station test: %s",
                        await data.configured_sources["gasbuddy"].get_site(916))

        _LOGGER.info("Fuels test: %s", await data.find_fuel_from_point(
            coordinates=(52.570419, 1.115850),
            radius=25.0,
            fuel_type="B7"
        )) #UK

        _LOGGER.info("Fuels test: %s", await data.find_fuel_from_point(
            coordinates=(39.2062720, 22.2513570),
            radius=30.0,
            fuel_type="95"
        )) #GR

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
