"""
Utilitarios de resiliencia: retry, backoff, tratamento de erros.

Fornece decorators para lidar com falhas transientes em APIs externas.
"""

import functools
import json
import random
import time
from typing import Any, Callable, Tuple, Type

import requests
import urllib3

from adb.core.config import (
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_RETRY_DELAY,
)
from adb.core.log import get_logger

# Logger tecnico - vai apenas para arquivo de log
logger = get_logger("adb.core.resilience")


# Excecoes transientes que justificam retry (rede, parsing, APIs instáveis)
TRANSIENT_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    # Rede/HTTP
    requests.RequestException,
    requests.ConnectionError,
    requests.Timeout,
    urllib3.exceptions.HTTPError,
    ConnectionError,
    TimeoutError,
    OSError,  # Inclui socket errors
    # Parsing (APIs que retornam resposta invalida/vazia)
    json.JSONDecodeError,
    ValueError,
)

# Alias para compatibilidade
NETWORK_EXCEPTIONS = TRANSIENT_EXCEPTIONS


def retry(
    max_attempts: int = DEFAULT_RETRY_ATTEMPTS,
    delay: float = DEFAULT_RETRY_DELAY,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    exceptions: Tuple[Type[Exception], ...] = TRANSIENT_EXCEPTIONS,
    jitter: bool = True,
) -> Callable:
    """
    Decorator para retry com exponential backoff e jitter.

    Args:
        max_attempts: Numero maximo de tentativas
        delay: Delay inicial em segundos
        backoff_factor: Multiplicador do delay apos cada falha
        exceptions: Tupla de excecoes para capturar (rede, parsing, etc)
        jitter: Se True, adiciona variacao aleatoria ao delay (evita thundering herd)

    Returns:
        Funcao decorada

    Example:
        @retry(max_attempts=3, delay=1.0)
        def fetch_data():
            return requests.get(url, timeout=30)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"Funcao {func.__name__} falhou apos {max_attempts} tentativas. "
                            f"Erro: {e}"
                        )
                        raise

                    # Calcular delay com jitter opcional
                    if jitter:
                        jitter_factor = random.uniform(0.5, 1.5)
                        sleep_time = current_delay * jitter_factor
                    else:
                        sleep_time = current_delay

                    logger.warning(
                        f"Tentativa {attempt}/{max_attempts} falhou para {func.__name__}. "
                        f"Retry em {sleep_time:.1f}s. Erro: {e}"
                    )

                    time.sleep(sleep_time)
                    current_delay *= backoff_factor

        return wrapper
    return decorator
