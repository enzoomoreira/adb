"""
Modulo MTE (interno) - Ministerio do Trabalho e Emprego.

Contem:
- caged: Microdados CAGED

Para coleta, use: adb.caged.collect()
Para query, use: adb.caged.read()
"""

# Apenas config exposto (para referencia)
from .caged import CAGED_CONFIG

__all__ = ['CAGED_CONFIG']
