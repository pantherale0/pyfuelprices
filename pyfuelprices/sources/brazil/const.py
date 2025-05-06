"""Brazil consts."""

from pyfuelprices.build_data import (
    GASPASS_URL
)

CONST_GET_FUELS = f"{GASPASS_URL}/api/v1/gaspass/"
CONST_FUELS = [
    "ultimo_preco_alcool",
    "ultimo_preco_diesel",
    "ultimo_preco_diesel_s10",
    "ultimo_preco_gasolina",
    "ultimo_preco_gasolina_adt",
    "ultimo_preco_gnv"
]
