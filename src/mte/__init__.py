"""
Modulo MTE (interno) - Ministerio do Trabalho e Emprego.

Contem:
- caged: Microdados CAGED

Para coleta, use: from core.collectors import collect
Para query, use: from core.data import caged
"""

# Apenas config exposto (para referencia)
from .caged import CAGED_CONFIG

__all__ = ['CAGED_CONFIG']
