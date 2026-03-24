"""
Funcoes genericas para manipulacao de indicadores.

Centraliza logica comum usada por todos os collectors.
"""


def get_config(config: dict, key: str) -> dict:
    """
    Retorna configuracao de um indicador.

    Args:
        config: Dicionario de configuracao do modulo (ex: SGS_CONFIG)
        key: Chave do indicador (ex: 'selic', 'ipca_anual')

    Returns:
        Dict com configuracao do indicador

    Raises:
        KeyError: Se indicador nao encontrado
    """
    if key not in config:
        available = ", ".join(config.keys())
        raise KeyError(f"Indicador '{key}' nao encontrado. Disponiveis: {available}")
    return config[key]
