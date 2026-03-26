"""Excecoes customizadas para o pacote adb.

Hierarquia:
    ADBException (base)
    +-- DataNotFoundError (dados nao encontrados)
    +-- APIError (erros de API externa)
"""


class ADBException(Exception):
    """Excecao base para o pacote adb."""

    pass


class DataNotFoundError(ADBException):
    """Dados solicitados nao existem ou nao foram encontrados."""

    pass


class APIError(ADBException):
    """Erro retornado por API externa."""

    pass
