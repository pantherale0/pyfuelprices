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
from .podpoint import PodPointSource
from .rontec import RontecUKSource
from .sainsburys import SainsburysUKSource
from .sgn import SgnRetailUKSource
from .shell import ShellUKSource
from .tesco import TescoUKSource

SOURCE_MAP: dict[str, tuple[Source, int, int, int]] = {
    "applegreen": (ApplegreenUKSource, 1, 1, 0),
    "asda": (AsdaUKSource, 1, 1, 0),
    "ascona": (AsconaGroupUKSource, 1, 1, 0),
    "bpuk": (BpUKSource, 1, 1, 0),
    "costco": (CostcoUKSource, 1, 1, 0),
    "essouk": (EssoUKSource, 1, 1, 0),
    "jet": (JetUKSource, 1, 0, 0),
    "karanretail": (KaranRetailSource, 1, 1, 0),
    "motoway": (MotowayUKSource, 1, 1, 0),
    "motorfuelgroup": (MotorFuelGroupUKSource, 1, 1, 0),
    "petrolprices": (PetrolPricesUKSource, 1, 1, 1),
    "podpoint": (PodPointSource, 1, 1, 0),
    "rontec": (RontecUKSource, 1, 1, 0),
    "sainsburys": (SainsburysUKSource, 1, 1, 0),
    "sgnretail": (SgnRetailUKSource, 1, 1, 0),
    "shelluk": (ShellUKSource, 1, 1, 0),
    "tesco": (TescoUKSource, 1, 1, 0)
}
