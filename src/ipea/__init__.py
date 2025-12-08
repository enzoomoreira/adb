"""
Modulo IPEA - Series temporais do IPEADATA.

Coleta de dados agregados (CAGED, desemprego, etc).
"""

from .client import IPEAClient
from .collector import IPEACollector
from .indicators import (
    IPEA_CONFIG,
    get_indicator_config,
    list_indicators,
    get_by_frequency,
    get_indicator_keys,
)

__all__ = [
    # Classes
    "IPEAClient",
    "IPEACollector",
    # Config
    "IPEA_CONFIG",
    # Helpers
    "get_indicator_config",
    "list_indicators",
    "get_by_frequency",
    "get_indicator_keys",
]
