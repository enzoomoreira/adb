"""
Modulo SGS (interno) - Series temporais do BCB.

Para coleta, use: from core.collectors import collect
Para query, use: from core.data import sgs
"""

# Apenas config exposto (para referencia)
from .indicators import SGS_CONFIG

__all__ = ['SGS_CONFIG']
