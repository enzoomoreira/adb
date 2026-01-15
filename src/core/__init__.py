"""
Modulo core - utilitarios compartilhados.

Contem:
- collectors: Classe base para coletores (BaseCollector)
- data: Gerenciador de persistencia (DataManager)
- indicators: Funcoes auxiliares para indicadores
- parallel: Executor paralelo (ParallelFetcher)
"""

from .collectors import BaseCollector
from .data import DataManager
from .indicators import get_indicator_config, list_indicators, filter_by_field

__all__ = [
    'BaseCollector',
    'DataManager',
    'get_indicator_config',
    'list_indicators',
    'filter_by_field',
]
