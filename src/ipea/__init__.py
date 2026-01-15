"""
Modulo IPEA - Series temporais do IPEADATA.

Coleta de dados agregados (CAGED, desemprego, etc).
"""

from .client import IPEAClient
from .collector import IPEACollector
from .indicators import IPEA_CONFIG

__all__ = [
    # Classes
    "IPEAClient",
    "IPEACollector",
    # Config
    "IPEA_CONFIG",
]
