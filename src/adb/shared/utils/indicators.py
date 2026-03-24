"""
Funcoes genericas para manipulacao de indicadores.

Centraliza logica comum usada por todos os modulos (sgs, expectations, ipea, sidra, bloomberg).
Cada modulo mantem seu CONFIG especifico e usa estas funcoes helper.
"""

from typing import Any


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

    Example:
        >>> from adb.shared.utils import get_config
        >>> from adb.bacen.sgs.indicators import SGS_CONFIG
        >>> config = get_config(SGS_CONFIG, 'selic')
        >>> config['code']
        432
    """
    if key not in config:
        available = ", ".join(config.keys())
        raise KeyError(f"Indicador '{key}' nao encontrado. Disponiveis: {available}")
    return config[key]


def list_keys(config: dict, frequency: str | None = None) -> list[str]:
    """
    Lista chaves de indicadores disponiveis.

    Args:
        config: Dicionario de configuracao do modulo
        frequency: Filtrar por frequencia ('daily', 'monthly', etc). None = todos.

    Returns:
        Lista de chaves de indicadores

    Example:
        >>> from adb.shared.utils import list_keys
        >>> from adb.bacen.sgs.indicators import SGS_CONFIG
        >>> list_keys(SGS_CONFIG)
        ['selic', 'cdi', 'dolar_ptax', ...]
        >>> list_keys(SGS_CONFIG, 'daily')
        ['selic', 'cdi', 'dolar_ptax', ...]
    """
    if frequency is None:
        return list(config.keys())
    return [key for key, cfg in config.items() if cfg.get("frequency") == frequency]


def filter_by(config: dict, field: str, value: Any) -> dict:
    """
    Filtra indicadores por um campo especifico.

    Args:
        config: Dicionario de configuracao do modulo
        field: Nome do campo para filtrar (ex: 'frequency', 'endpoint')
        value: Valor do campo

    Returns:
        Dict com indicadores filtrados

    Example:
        >>> from adb.shared.utils import filter_by
        >>> from adb.bacen.sgs.indicators import SGS_CONFIG
        >>> daily_indicators = filter_by(SGS_CONFIG, 'frequency', 'daily')
    """
    return {key: cfg for key, cfg in config.items() if cfg.get(field) == value}
