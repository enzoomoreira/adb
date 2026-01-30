"""
Camada de servicos - orquestracao de operacoes.

Contem:
- collectors: BaseCollector e registry para coleta de dados
"""

from .collectors import BaseCollector

__all__ = [
    "BaseCollector",
]
