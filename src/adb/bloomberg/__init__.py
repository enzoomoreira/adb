"""
Modulo Bloomberg (interno) - Dados de mercado.

Para coleta, use: adb.bloomberg.collect()
Para query, use: adb.bloomberg.read()
"""

from .indicators import BLOOMBERG_CONFIG

__all__ = ['BLOOMBERG_CONFIG']
