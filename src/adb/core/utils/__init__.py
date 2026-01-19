"""
Utilitarios compartilhados do core.

Contem:
- indicators: Funcoes para manipulacao de configs de indicadores
- parallel: Executor paralelo para tarefas I/O bound
- dates: Funcoes para parsing e validacao de datas
"""

from .indicators import get_indicator_config, list_indicators, filter_by_field
from .dates import parse_date, normalize_date_index

__all__ = [
    'get_indicator_config',
    'list_indicators',
    'filter_by_field',
    'parse_date',
    'normalize_date_index',
]
