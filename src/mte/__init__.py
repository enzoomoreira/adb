"""
Modulo MTE - Ministerio do Trabalho e Emprego.

Fornece acesso a dados publicos do MTE, incluindo CAGED.
"""

from .caged import (
    CAGEDClient,
    CAGEDCollector,
    CAGED_CONFIG,
    list_indicators,
    get_indicator_config,
)

__all__ = [
    'CAGEDClient',
    'CAGEDCollector',
    'CAGED_CONFIG',
    'list_indicators',
    'get_indicator_config',
]
