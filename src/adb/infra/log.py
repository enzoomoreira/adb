"""
Configuracao centralizada de logging para o projeto.

Usa lazy initialization para evitar carregamento de dependencias
ate que logging seja realmente necessario.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loguru import Logger

_configured: bool = False
_logger_instance: "Logger | None" = None


def _ensure_configured():
    """
    Configura logging na primeira necessidade (lazy).

    Imports tardios de loguru e config para evitar carregamento
    no import time do modulo.
    """
    global _configured, _logger_instance

    if _configured:
        return

    # Imports tardios - so carrega quando realmente precisar
    from datetime import datetime
    from loguru import logger
    from adb.infra.config import get_settings

    logs_path = get_settings().logs_path

    # Remove handler padrao do loguru (console colorido)
    logger.remove()

    # File handler com rotacao (10MB max, 30 dias retencao)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_path / f"adb_{today}.log"

    logger.add(
        log_file,
        format="[{time:YYYY-MM-DD HH:mm:ss}] {level} [{name}] {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
    )

    _logger_instance = logger
    _configured = True


def get_logger(name: str) -> "Logger":
    """
    Retorna logger configurado para o modulo especificado.

    Configura o logger na primeira chamada (lazy initialization).
    Logs vao para {data_dir}/../Logs/adb_YYYY-MM-DD.log

    O arquivo .log contem informacoes tecnicas para debugging:
    - Timestamps precisos
    - Niveis (DEBUG, INFO, WARNING, ERROR)
    - Nome do modulo
    - Stack traces de erros

    Para output visual ao usuario, use Display de adb.ui.display.

    Args:
        name: Nome do logger (geralmente __name__ ou nome da classe)

    Returns:
        Logger loguru com contexto do modulo
    """
    _ensure_configured()
    assert _logger_instance is not None
    return _logger_instance.bind(name=name)
