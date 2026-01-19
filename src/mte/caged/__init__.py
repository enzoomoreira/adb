"""
Modulo CAGED (interno) - Microdados do MTE.

Para coleta, use: from core.collectors import collect
Para query, use: from core.data import caged

Exemplo:
    from core.data import caged
    
    df = caged.read(year=2025)
    periodos = caged.available_periods()
"""

from .indicators import CAGED_CONFIG

__all__ = ['CAGED_CONFIG']
