"""
Camada de infraestrutura - I/O, configs, retry, persistencia.

Contem:
- config: Configuracoes e paths (platformdirs)
- log: Logging usando loguru
- resilience: Retry e backoff usando tenacity
- persistence: Persistencia de dados (DataManager, QueryEngine)
"""

from .config import get_settings
from .log import get_logger
from .resilience import retry

__all__ = [
    # Config
    "get_settings",
    # Log
    "get_logger",
    # Resilience
    "retry",
]
