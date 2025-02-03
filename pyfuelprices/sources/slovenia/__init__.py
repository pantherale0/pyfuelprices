"""Argentina data sources."""

from .goriva import GorivaSource

SOURCE_MAP = {
    "goriva": (GorivaSource, 1, 1,)
}
