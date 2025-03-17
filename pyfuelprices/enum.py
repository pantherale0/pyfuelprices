"""pyfuelprices enum."""

from enum import StrEnum

class UnitMode(StrEnum):
    """Define set unit modes."""
    MILE="mile"
    KILOMETRE="kilometre"
    METRE="metre"

class SupportsConfigType(StrEnum):
    """Define the type of configurations a datasource supports."""
    REQUIRES_ONLY="requires_only"
    OPTIONAL_ONLY="optional_only"
    REQUIRES_AND_OPTIONAL="requires_and_optional"
    NONE="none"
