"""
Modulo BACEN (interno) - Dados do Banco Central do Brasil.

Contem:
- sgs: Series temporais SGS
- expectations: Expectativas Focus

Para coleta, use: adb.sgs.collect() ou adb.expectations.collect()
Para query, use: adb.sgs.read() ou adb.expectations.read()
"""

# Apenas configs expostos (para referencia)
from .sgs import SGS_CONFIG
from .expectations import EXPECTATIONS_CONFIG

__all__ = [
    'SGS_CONFIG',
    'EXPECTATIONS_CONFIG',
]
