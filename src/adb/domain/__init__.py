"""
Camada de dominio - regras de negocio e entidades.

Contem:
- exceptions: Excecoes de dominio
- explorers: BaseExplorer (logica de leitura de dados)
- schemas: Schemas Pydantic para validacao
"""

from .exceptions import (
    ADBException,
    DataNotFoundError,
    APIError,
    RateLimitError,
    ConnectionFailedError,
)
from .explorers import BaseExplorer
from .schemas import (
    IndicatorConfig,
    SGSIndicatorConfig,
    IPEAIndicatorConfig,
    SIDRAIndicatorConfig,
    validate_indicator_config,
)

__all__ = [
    # Exceptions
    "ADBException",
    "DataNotFoundError",
    "APIError",
    "RateLimitError",
    "ConnectionFailedError",
    # Explorers
    "BaseExplorer",
    # Schemas
    "IndicatorConfig",
    "SGSIndicatorConfig",
    "IPEAIndicatorConfig",
    "SIDRAIndicatorConfig",
    "validate_indicator_config",
]
