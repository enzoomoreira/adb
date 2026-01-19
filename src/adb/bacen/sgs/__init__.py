"""
Modulo SGS (interno) - Series temporais do BCB.

Para coleta, use: adb.sgs.collect()
Para query, use: adb.sgs.read()
"""

# Apenas config exposto (para referencia)
from .indicators import SGS_CONFIG

__all__ = ['SGS_CONFIG']
