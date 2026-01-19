"""
Modulo core - API centralizada do agora-database.

Query:
    from adb.core.data import sgs, caged, expectations, ipea, bloomberg, sidra

    df = sgs.read('selic', start='2020')
    df = caged.read(year=2025, uf=35)

Classes (uso avancado):
    from adb.core.data import QueryEngine, DataManager
    from adb.core.collectors import BaseCollector
"""

# API de coleta (apenas base class)
from .collectors import BaseCollector

# API de dados
from .data import DataManager, QueryEngine

# Utilitarios
from .utils import get_indicator_config, list_indicators, filter_by_field

# Config global
from .config import PROJECT_ROOT, DATA_PATH

__all__ = [
    # Coleta
    'BaseCollector',
    # Dados
    'DataManager',
    'QueryEngine',
    # Utilitarios
    'get_indicator_config',
    'list_indicators',
    'filter_by_field',
    # Config
    'PROJECT_ROOT',
    'DATA_PATH',
]
