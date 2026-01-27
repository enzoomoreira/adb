"""
Excecoes customizadas para o pacote adb.

Hierarquia:
    ADBException (base)
    ├── DataNotFoundError (dados nao encontrados)
    └── APIError (erros de API externa)
        ├── RateLimitError (limite de requisicoes)
        └── ConnectionFailedError (falha de conexao)
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


class RateLimitError(APIError):
    """Limite de requisicoes excedido pela API."""
    pass


class ConnectionFailedError(APIError):
    """Falha de conexao com servico externo."""
    pass
