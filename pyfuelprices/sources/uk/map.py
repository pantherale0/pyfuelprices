"""Hold source mappings for modules."""

from pyfuelprices.sources import Source
from .applegreenstores import ApplegreenUKSource
from .ascona import AsconaGroupUKSource
from .asda import AsdaUKSource
from .bpuk import BpUKSource
from .essouk import EssoUKSource
from .jet import JetUKSource
from .morrisons import MorrisonsUKSource
from .moto import MotowayUKSource
from .motorfuelgroup import MotorFuelGroupUKSource
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
    "essouk": EssoUKSource,
    "jet": JetUKSource,
    "morrisons": MorrisonsUKSource,
    "motoway": MotowayUKSource,
    "motorfuelgroup": MotorFuelGroupUKSource,
    "rontec": RontecUKSource,
    "sainsburys": SainsburysUKSource,
    "sgnretail": SgnRetailUKSource,
    "shelluk": ShellUKSource,
    "tesco": TescoUKSource
}
