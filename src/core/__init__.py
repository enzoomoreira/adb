"""
Modulo core - API centralizada do agora-database.

Coleta:
    from core.collectors import collect, available_sources, get_status
    
    collect('sgs')
    collect('caged', year=2025)

Query:
    from core.data import sgs, caged, expectations, ipea, bloomberg
    
    df = sgs.read('selic', start='2020')
    df = caged.read(year=2025, uf=35)

Classes (uso avancado):
    from core.data import QueryEngine, DataManager
    from core.collectors import BaseCollector
"""

# API de coleta
from .collectors import collect, available_sources, get_status, BaseCollector

# API de dados
from .data import DataManager, QueryEngine

# Utilitarios
from .utils import get_indicator_config, list_indicators, filter_by_field

# Config global
from .config import PROJECT_ROOT, DATA_PATH

__all__ = [
    # Coleta
    'collect',
    'available_sources',
    'get_status',
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
