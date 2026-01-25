"""
Modulo CAGED (interno) - Microdados do MTE.

Para coleta, use: adb.caged.collect()
Para query, use: adb.caged.read()

Exemplo:
    import adb
    
    df = adb.caged.read(year=2025)
    periodos = adb.caged.available_periods()
"""

from .indicators import CAGED_CONFIG

__all__ = ['CAGED_CONFIG']
