"""
Modulo CAGED - Cadastro Geral de Empregados e Desempregados.

Coleta de microdados do Novo CAGED via FTP do MTE.
"""

from .client import CAGEDClient
from .collector import CAGEDCollector
from .indicators import (
    CAGED_CONFIG,
    get_available_periods,
)

__all__ = [
    'CAGEDClient',
    'CAGEDCollector',
    'CAGED_CONFIG',
    'get_available_periods',
]
