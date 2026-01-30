"""
Modulo core - Componentes internos do agora-database.

API publica via pacote principal:
    import adb
    adb.sgs.read('selic')
    adb.caged.read(year=2024)

Classes para uso avancado:
    from adb import QueryEngine, DataManager
"""

# API de coleta (apenas base class, uso interno)
from .collectors import BaseCollector

# API de dados
from .data import DataManager, QueryEngine

# Display (output visual ao usuario, uso interno)
from .display import Display, get_display

# Config global
from .config import PROJECT_ROOT, DATA_PATH

# Schemas Pydantic para validacao
from .schemas import (
    IndicatorConfig,
    SGSIndicatorConfig,
    IPEAIndicatorConfig,
    SIDRAIndicatorConfig,
    validate_indicator_config,
)

__all__ = [
    # Coleta (interno)
    'BaseCollector',
    # Dados
    'DataManager',
    'QueryEngine',
    # Display (interno)
    'Display',
    'get_display',
    # Config
    'PROJECT_ROOT',
    'DATA_PATH',
    # Schemas
    'IndicatorConfig',
    'SGSIndicatorConfig',
    'IPEAIndicatorConfig',
    'SIDRAIndicatorConfig',
    'validate_indicator_config',
]
