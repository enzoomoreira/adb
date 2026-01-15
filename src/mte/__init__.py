"""
Modulo MTE - Ministerio do Trabalho e Emprego.

Fornece acesso a dados publicos do MTE, incluindo CAGED.
"""

from .caged import (
    CAGEDClient,
    CAGEDCollector,
    CAGED_CONFIG,
)

__all__ = [
    'CAGEDClient',
    'CAGEDCollector',
    'CAGED_CONFIG',
]
