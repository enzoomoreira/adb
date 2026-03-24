"""
Camada de dominio - regras de negocio e entidades.

Contem:
- exceptions: Excecoes de dominio
- explorers: BaseExplorer (logica de leitura de dados)
"""

from .exceptions import (
    ADBException,
    DataNotFoundError,
    APIError,
    RateLimitError,
    ConnectionFailedError,
)
from .explorers import BaseExplorer

__all__ = [
    # Exceptions
    "ADBException",
    "DataNotFoundError",
    "APIError",
    "RateLimitError",
    "ConnectionFailedError",
    # Explorers
    "BaseExplorer",
]
