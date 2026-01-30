"""
Camada de infraestrutura - I/O, configs, retry, persistencia.

Contem:
- config: Configuracoes e paths do projeto
- log: Logging usando loguru
- resilience: Retry e backoff usando tenacity
- persistence: Persistencia de dados (DataManager, QueryEngine)
"""

from .config import PROJECT_ROOT, DATA_PATH, OUTPUTS_PATH
from .log import get_logger
from .resilience import retry

__all__ = [
    # Config
    "PROJECT_ROOT",
    "DATA_PATH",
    "OUTPUTS_PATH",
    # Log
    "get_logger",
    # Resilience
    "retry",
]
