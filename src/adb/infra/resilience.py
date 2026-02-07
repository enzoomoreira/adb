"""
Utilitarios de resiliencia: retry, backoff, tratamento de erros.

Fornece decorators para lidar com falhas transientes em APIs externas.
Usa tenacity para implementacao robusta de retry com exponential backoff.
"""

import json
from typing import Tuple, Type

import requests
import urllib3
from tenacity import (
    retry as tenacity_retry,
    stop_after_attempt,
    wait_exponential,
    wait_random_exponential,
    retry_if_exception_type,
    RetryCallState,
)

from adb.infra.config import (  # ATUALIZADO
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_RETRY_DELAY,
)

# Logger lazy - so carrega quando usado
_logger = None


def _get_logger():
    """Logger lazy - so carrega quando usado."""
    global _logger
    if _logger is None:
        from adb.infra.log import get_logger  # ATUALIZADO

        _logger = get_logger("adb.infra.resilience")
    return _logger


def _before_sleep_log(retry_state: RetryCallState):
    """
    Callback para logar antes de dormir entre tentativas.

    Usa loguru ao inves do before_sleep_log padrao do tenacity.
    """
    if retry_state.outcome is None:
        return

    exception = retry_state.outcome.exception()
    fn_name = retry_state.fn.__name__ if retry_state.fn else "unknown"
    _get_logger().warning(
        f"Tentativa {retry_state.attempt_number} falhou para {fn_name}. "
        f"Retry em {retry_state.upcoming_sleep:.1f}s. Erro: {exception}"
    )


def _log_final_failure(retry_state: RetryCallState):
    """
    Callback quando todas tentativas falharam.

    Loga erro final e re-levanta a excecao original.
    Este callback e necessario pois before_sleep nao e chamado na ultima
    tentativa (nao ha sleep apos a falha final).
    """
    if retry_state.outcome is None:
        return
    exception = retry_state.outcome.exception()
    fn_name = retry_state.fn.__name__ if retry_state.fn else "unknown"
    _get_logger().error(
        f"Funcao {fn_name} falhou apos "
        f"{retry_state.attempt_number} tentativas. Erro: {exception}"
    )
    # Re-levanta a excecao original
    raise retry_state.outcome.result()


# Excecoes transientes que justificam retry (rede, parsing, APIs instaveis)
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
):
    """
    Decorator para retry com exponential backoff e jitter.

    Usa tenacity internamente para implementacao robusta.

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
    # Calcula delay maximo baseado nos parametros
    # Com 3 tentativas e backoff 2.0: delays podem ser 1, 2, 4 -> max ~4s
    max_delay = delay * (backoff_factor ** (max_attempts - 1))

    # Seleciona estrategia de wait baseado em jitter
    if jitter:
        wait_strategy = wait_random_exponential(multiplier=delay, max=max_delay)
    else:
        wait_strategy = wait_exponential(multiplier=delay, max=max_delay)

    return tenacity_retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_strategy,
        retry=retry_if_exception_type(exceptions),
        before_sleep=_before_sleep_log,
        retry_error_callback=_log_final_failure,
        reraise=True,  # Re-levanta excecao original apos todas tentativas
    )
