"""
Configuracao centralizada de logging para o projeto.

Usa loguru para logging simplificado com rotacao automatica.
Logs sao salvos em {PROJECT_ROOT}/logs/ com rotacao automatica.
"""

from datetime import datetime

from loguru import logger

from adb.core.config import LOG_PATH

# Criar diretorio de logs uma vez no import
LOG_PATH.mkdir(exist_ok=True)

# Flag para evitar configuracao duplicada
_configured = False


def _configure_logger():
    """
    Configura loguru na primeira chamada de get_logger() (lazy initialization).

    Remove handler padrao e adiciona file handler com rotacao.
    Console handler foi removido - usar Display para output visual.
    """
    global _configured
    if _configured:
        return

    # Remove handler padrao do loguru (console colorido)
    logger.remove()

    # File handler com rotacao (10MB max, 30 dias retencao)
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = LOG_PATH / f"adb_{today}.log"

    logger.add(
        log_file,
        format="[{time:YYYY-MM-DD HH:mm:ss}] {level} [{name}] {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
    )

    _configured = True


def get_logger(name: str):
    """
    Retorna logger configurado para o modulo especificado.

    Configura o logger na primeira chamada (lazy initialization).
    Logs vao para {PROJECT_ROOT}/logs/adb_YYYY-MM-DD.log

    O arquivo .log contem informacoes tecnicas para debugging:
    - Timestamps precisos
    - Niveis (DEBUG, INFO, WARNING, ERROR)
    - Nome do modulo
    - Stack traces de erros

    Para output visual ao usuario, use Display de core.display.

    Args:
        name: Nome do logger (geralmente __name__ ou nome da classe)

    Returns:
        Logger loguru com contexto do modulo
    """
    _configure_logger()
    return logger.bind(name=name)
