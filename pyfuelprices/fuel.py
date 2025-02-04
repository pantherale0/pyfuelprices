"""Representation of a single fuel."""

class Fuel:
    """Individual Fuel."""

    _fuel_type: str
    _cost: float
    _props: dict

    def __init__(self, fuel_type: str, cost: float, props: dict=None):
        """Initalize a fuel price."""
        self._fuel_type = fuel_type
        if cost is None:
            self._cost = 0
        else:
            self._cost = cost
        self._props = props

    @property
    def __dict__(self) -> dict:
        """Convert to a dict."""
        return {
            "type": self._fuel_type,
            "cost": self._cost,
            "props": self._props
        }

    def update(self, fuel_type: str, cost: float, props: dict):
        """Update this instance of data."""
        self._fuel_type = fuel_type
        if cost is None:
            self._cost = 0
        else:
            self._cost = cost
        self._props = props

    @property
    def fuel_type(self) -> str:
        return self._fuel_type

    @property
    def cost(self) -> float:
        return self._cost

    @property
    def props(self) -> dict | None:
        return self._props
