"""
Modulo de collectors - classes base para coleta de dados.

Uso:
    # Coleta via explorers (API publica)
    from adb.core.data import sgs, caged
    sgs.collect()
    caged.collect(max_workers=4)

    # Base class (para criar novos collectors)
    from adb.core.collectors import BaseCollector
"""

from .base import BaseCollector

__all__ = ['BaseCollector']
