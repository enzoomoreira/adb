"""
Configuracao centralizada de logging para o projeto.

Logs sao salvos em {PROJECT_ROOT}/logs/ com rotacao automatica.
"""

import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

from adb.core.config import LOG_PATH

# Criar diretorio de logs uma vez no import (nao em cada get_logger)
LOG_PATH.mkdir(exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """
    Retorna logger configurado apenas para arquivo.

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
        logging.Logger configurado (apenas file handler)
    """
    logger = logging.getLogger(name)

    # Se logger ja tem handlers, assume que ja esta configurado
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Formatter para arquivo (detalhado)
    file_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File Handler com rotacao (10MB max, 5 backups)
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = LOG_PATH / f"adb_{today}.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler removido - usar Display para output visual

    return logger
