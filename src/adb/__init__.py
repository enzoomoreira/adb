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

# Classes (para uso avancado)
from adb.infra.persistence import QueryEngine, DataManager

# Config
from adb.infra.config import PROJECT_ROOT, DATA_PATH, OUTPUTS_PATH

# Explorers (namespaces de query/coleta) - via lazy loading
_sgs = None
_caged = None
_expectations = None
_ipea = None
_bloomberg = None
_sidra = None


def __getattr__(name):
    """Lazy loading dos explorers."""
    global _sgs, _caged, _expectations, _ipea, _bloomberg, _sidra

    if name == 'sgs':
        if _sgs is None:
            from adb.providers.bacen.sgs.explorer import SGSExplorer
            _sgs = SGSExplorer()
        return _sgs

    if name == 'caged':
        if _caged is None:
            from adb.providers.mte.caged.explorer import CAGEDExplorer
            _caged = CAGEDExplorer()
        return _caged

    if name == 'expectations':
        if _expectations is None:
            from adb.providers.bacen.expectations.explorer import ExpectationsExplorer
            _expectations = ExpectationsExplorer()
        return _expectations

    if name == 'ipea':
        if _ipea is None:
            from adb.providers.ipea.explorer import IPEAExplorer
            _ipea = IPEAExplorer()
        return _ipea

    if name == 'bloomberg':
        if _bloomberg is None:
            from adb.providers.bloomberg.explorer import BloombergExplorer
            _bloomberg = BloombergExplorer()
        return _bloomberg

    if name == 'sidra':
        if _sidra is None:
            from adb.providers.ibge.sidra.explorer import SidraExplorer
            _sidra = SidraExplorer()
        return _sidra

    raise AttributeError(f"module 'adb' has no attribute '{name}'")


def available_sources() -> list[str]:
    """Lista todas as fontes de dados disponiveis."""
    return ['sgs', 'caged', 'expectations', 'ipea', 'bloomberg', 'sidra']



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
