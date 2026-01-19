"""
Registry centralizado de collectors.

Permite coleta via: collect('sgs'), collect('caged', year=2025)
"""

from typing import Any
import importlib


# Mapeamento de nomes para collectors (lazy import)
_COLLECTOR_MAP = {
    'sgs': ('bacen.sgs.collector', 'SGSCollector'),
    'expectations': ('bacen.expectations.collector', 'ExpectationsCollector'),
    'caged': ('mte.caged.collector', 'CAGEDCollector'),
    'ipea': ('ipea.collector', 'IPEACollector'),
    'bloomberg': ('bloomberg.collector', 'BloombergCollector'),
}


def _get_collector(name: str):
    """
    Importa e retorna classe do collector (lazy).

    Args:
        name: Nome do collector

    Returns:
        Classe do collector

    Raises:
        ValueError: Se collector nao encontrado
    """
    if name not in _COLLECTOR_MAP:
        available = ', '.join(_COLLECTOR_MAP.keys())
        raise ValueError(f"Collector '{name}' nao encontrado. Disponiveis: {available}")

    module_path, class_name = _COLLECTOR_MAP[name]

    # Import dinamico
    module = importlib.import_module(module_path)
    collector_class = getattr(module, class_name)

    return collector_class


def collect(
    source: str,
    indicators: str | list[str] = 'all',
    save: bool = True,
    verbose: bool = True,
    **kwargs,
) -> None:
    """
    Coleta dados de uma fonte e salva em Parquet.

    Args:
        source: Nome da fonte ('sgs', 'caged', 'expectations', 'ipea', 'bloomberg')
        indicators: Indicadores a coletar ('all', lista, ou string unico)
        save: Se True, salva em Parquet
        verbose: Se True, imprime progresso
        **kwargs: Argumentos especificos da fonte:
            - CAGED: year, month, parallel, max_workers
            - Expectations: start_date, limit

    Examples:
        >>> collect('sgs')  # Todos indicadores SGS
        >>> collect('sgs', indicators='selic')  # Um indicador
        >>> collect('caged', year=2025)  # CAGED ano inteiro
        >>> collect('caged', year=2025, month=10)  # CAGED mes especifico
        >>> collect('expectations')  # Focus BCB
        >>> collect('ipea')  # IPEA
    """
    collector_class = _get_collector(source)
    collector = collector_class()  # DATA_PATH automatico via BaseCollector

    # Extrair kwargs especificos do collect()
    collect_kwargs = {'indicators': indicators, 'save': save, 'verbose': verbose}

    # Passar kwargs extras (year, month, etc) para o collector
    collect_kwargs.update(kwargs)

    collector.collect(**collect_kwargs)


def available_sources() -> list[str]:
    """
    Retorna lista de fontes disponiveis.

    Returns:
        Lista de nomes de fontes

    Examples:
        >>> available_sources()
        ['sgs', 'expectations', 'caged', 'ipea', 'bloomberg']
    """
    return list(_COLLECTOR_MAP.keys())


def get_status(source: str):
    """
    Retorna status dos dados de uma fonte.

    Args:
        source: Nome da fonte

    Returns:
        DataFrame ou dict com status dos dados

    Examples:
        >>> get_status('sgs')  # Status dos arquivos SGS
        >>> get_status('caged')  # Periodos CAGED coletados
    """
    collector_class = _get_collector(source)
    collector = collector_class()
    return collector.get_status()
