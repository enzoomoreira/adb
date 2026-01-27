"""
Configuracao centralizada de logging para o projeto.

Logs sao salvos em {PROJECT_ROOT}/logs/ com rotacao automatica.
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

from adb.core.config import LOG_PATH

# Criar diretorio de logs uma vez no import (nao em cada get_logger)
LOG_PATH.mkdir(exist_ok=True)


def get_logger(name: str, verbose: bool = True) -> logging.Logger:
    """
    Retorna instancia de logger configurada.

    Args:
        name: Nome do logger (geralmente __name__ ou nome da classe)
        verbose: Se True, adiciona handler de console (nivel INFO)

    Returns:
        logging.Logger configurado
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

    # Console Handler (nivel INFO - visivel ao usuario)
    if verbose:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        # Formato simples para console (compativel com prints antigos)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger
