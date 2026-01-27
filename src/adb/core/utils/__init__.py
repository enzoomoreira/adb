"""
Utilitarios compartilhados do core.

Contem:
- indicators: Funcoes para manipulacao de configs de indicadores
- parallel: Executor paralelo para tarefas I/O bound
- dates: Funcoes para parsing e validacao de datas
"""

from .indicators import get_config, list_keys, filter_by
from .dates import parse_date, normalize_index

__all__ = [
    'get_config',
    'list_keys',
    'filter_by',
    'parse_date',
    'normalize_index',
]
