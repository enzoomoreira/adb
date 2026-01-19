"""
Modulo BACEN (interno) - Dados do Banco Central do Brasil.

Contem:
- sgs: Series temporais SGS
- expectations: Expectativas Focus

Para coleta, use: from core.collectors import collect
Para query, use: from core.data import sgs, expectations
"""

# Apenas configs expostos (para referencia)
from .sgs import SGS_CONFIG
from .expectations import EXPECTATIONS_CONFIG

__all__ = [
    'SGS_CONFIG',
    'EXPECTATIONS_CONFIG',
]
