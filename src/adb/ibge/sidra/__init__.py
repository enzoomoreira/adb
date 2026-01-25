"""
Modulo IBGE Sidra (interno) - Dados do IBGE via API Sidra.

Para coleta, use: adb.sidra.collect()
Para query, use: adb.sidra.read()
"""

from .indicators import SIDRA_CONFIG
from .collector import SidraCollector

__all__ = ['SIDRA_CONFIG', 'SidraCollector']
