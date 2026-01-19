"""
Modulo IPEA (interno) - Series IPEADATA.

Para coleta, use: adb.ipea.collect()
Para query, use: adb.ipea.read()
"""

from .indicators import IPEA_CONFIG

__all__ = ['IPEA_CONFIG']
