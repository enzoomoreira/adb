"""
Modulo Bloomberg - Market Data.

Coleta de dados de mercado via Bloomberg Terminal (xbbg).
"""

from .client import BloombergClient
from .collector import BloombergCollector
from .indicators import BLOOMBERG_CONFIG, LOOKBACK_DAYS

__all__ = [
    "BloombergClient",
    "BloombergCollector",
    "BLOOMBERG_CONFIG",
    "LOOKBACK_DAYS",
]
