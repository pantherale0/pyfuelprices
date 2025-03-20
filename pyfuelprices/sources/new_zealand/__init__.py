"""New Zealand sources."""

from pyfuelprices.sources.australia.petrolspy import PetrolSpySource
from .finelly import FinellyDataSource

SOURCE_MAP = {
    "finelly": (FinellyDataSource, 1, 1, 0,),
    "petrolspy": (PetrolSpySource, 1, 1,),
}
