"""
Modulo IBGE Sidra.
"""

from .indicators import SIDRA_CONFIG
from .collector import SidraCollector

__all__ = ['SIDRA_CONFIG', 'SidraCollector']
