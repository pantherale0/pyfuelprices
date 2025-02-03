"""Argentina data sources."""

from .const import AR_GOB_ENERGY_ID

from .gobenergy import GobEnergySource

SOURCE_MAP = {
    AR_GOB_ENERGY_ID: (GobEnergySource, 1, 1,)
}
