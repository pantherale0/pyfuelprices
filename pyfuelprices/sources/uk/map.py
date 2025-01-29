"""Hold source mappings for modules."""

from pyfuelprices.sources import Source
from .applegreenstores import ApplegreenUKSource
from .ascona import AsconaGroupUKSource
from .asda import AsdaUKSource
from .bpuk import BpUKSource
from .costco import CostcoUKSource
from .essouk import EssoUKSource
from .jet import JetUKSource
from .karanretail import KaranRetailSource
from .moto import MotowayUKSource
from .motorfuelgroup import MotorFuelGroupUKSource
from .petrolprices import PetrolPricesUKSource
from .rontec import RontecUKSource
from .sainsburys import SainsburysUKSource
from .sgn import SgnRetailUKSource
from .shell import ShellUKSource
from .tesco import TescoUKSource

SOURCE_MAP: dict[str, Source] = {
    "applegreen": ApplegreenUKSource,
    "asda": AsdaUKSource,
    "ascona": AsconaGroupUKSource,
    "bpuk": BpUKSource,
    "costco": CostcoUKSource,
    "essouk": EssoUKSource,
    "jet": JetUKSource,
    "karanretail": KaranRetailSource,
    "motoway": MotowayUKSource,
    "motorfuelgroup": MotorFuelGroupUKSource,
    "petrolprices": PetrolPricesUKSource,
    "rontec": RontecUKSource,
    "sainsburys": SainsburysUKSource,
    "sgnretail": SgnRetailUKSource,
    "shelluk": ShellUKSource,
    "tesco": TescoUKSource
}
