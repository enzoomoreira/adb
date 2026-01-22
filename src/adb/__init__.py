"""
agora-database - Coleta e consulta de dados economicos brasileiros.

Uso:
    import adb

    # Query
    df = adb.sgs.read('selic', start='2020')
    df = adb.caged.read(year=2025, uf=35)

    # Coleta
    adb.sgs.collect()
    adb.caged.collect(max_workers=8)

Fontes disponiveis:
    - sgs: Series temporais BCB (Selic, CDI, PTAX, IBC-Br, IGP-M)
    - expectations: Expectativas Focus BCB (IPCA, PIB, Cambio, Selic)
    - caged: Microdados CAGED/MTE (admissoes, desligamentos)
    - ipea: Series agregadas IPEADATA
    - bloomberg: Dados de mercado (requer terminal)
    - sidra: Series IBGE Sidra (IPCA, PIB, etc.)
"""

# Explorers (namespaces de query/coleta) - via lazy loading
from adb.core.data import sgs, caged, expectations, ipea, bloomberg, sidra

# Classes (para uso avancado)
from adb.core.data import QueryEngine, DataManager

# Config
from adb.core.config import PROJECT_ROOT, DATA_PATH, OUTPUTS_PATH


def available_sources() -> list[str]:
    """Lista todas as fontes de dados disponiveis."""
    return ['sgs', 'caged', 'expectations', 'ipea', 'bloomberg', 'sidra']


def __getattr__(name):
    if name == 'charting':
        from adb.core import charting
        return charting
    raise AttributeError(f"module 'adb' has no attribute '{name}'")


__all__ = [
    # Explorers
    'sgs',
    'caged',
    'expectations',
    'ipea',
    'bloomberg',
    'sidra',
    # Classes
    'QueryEngine',
    'DataManager',
    # Config
    'PROJECT_ROOT',
    'DATA_PATH',
    'OUTPUTS_PATH',
    # Helpers
    'available_sources',
]
