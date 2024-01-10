"""Representation of a single fuel."""

class Fuel:
    """Individual Fuel."""

    def __init__(self, fuel_type: str, cost: float, props: dict):
        """Initalize a fuel price."""
        self.fuel_type = fuel_type
        if cost is None:
            self.cost = 0
        else:
            self.cost = cost
        self.props = props

    def __dict__(self) -> dict:
        """Convert to a dict."""
        return {
            "type": self.fuel_type,
            "cost": self.cost,
            "properties": self.props
        }

    def update(self, fuel_type: str, cost: float, props: dict):
        """Update this instance of data."""
        self.fuel_type = fuel_type
        if cost is None:
            self.cost = 0
        else:
            self.cost = cost
        self.props = props
