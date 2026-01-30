"""
Schemas Pydantic para validacao de dados e configuracoes.

Fornece validacao em runtime para indicadores e configuracoes do projeto.
"""

from .indicators import (
    IndicatorConfig,
    SGSIndicatorConfig,
    IPEAIndicatorConfig,
    SIDRAIndicatorConfig,
    validate_indicator_config,
)

__all__ = [
    "IndicatorConfig",
    "SGSIndicatorConfig",
    "IPEAIndicatorConfig",
    "SIDRAIndicatorConfig",
    "validate_indicator_config",
]
