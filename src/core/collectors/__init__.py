"""
Modulo de collectors - coleta centralizada de dados.

Uso:
    from core.collectors import collect, available_sources, get_status

    # Listar fontes disponiveis
    available_sources()  # ['sgs', 'expectations', 'caged', 'ipea', 'bloomberg']

    # Coletar dados
    collect('sgs')
    collect('sgs', indicators='selic')
    collect('caged', year=2025)
    collect('caged', year=2025, month=10)

    # Verificar status
    get_status('sgs')
"""

from .base import BaseCollector
from .registry import collect, available_sources, get_status

__all__ = [
    'BaseCollector',
    'collect',
    'available_sources',
    'get_status',
]
