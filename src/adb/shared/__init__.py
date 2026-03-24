"""
Utilitarios compartilhados - funcoes puras cross-cutting.

Contem:
- utils: Utilitarios para datas, indicadores, etc.
"""

from .utils import get_config, parse_date, normalize_index

__all__ = [
    "get_config",
    "parse_date",
    "normalize_index",
]
