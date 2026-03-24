"""
adb - Acesso unificado a dados economicos brasileiros.

Uso:
    import adb

    # Fetch direto da API (stateless, sem disco)
    df = adb.sgs.fetch('selic', start='2020')

    # Cache local (coleta + leitura de disco)
    adb.sgs.collect()
    df = adb.sgs.read('selic', start='2020')

Fontes disponiveis:
    - sgs: Series temporais BCB (Selic, CDI, PTAX, IBC-Br, IGP-M)
    - expectations: Expectativas Focus BCB (IPCA, PIB, Cambio, Selic)
    - ipea: Series agregadas IPEADATA
    - bloomberg: Dados de mercado (requer terminal)
    - sidra: Series IBGE Sidra (IPCA, PIB, etc.)
"""

# Config
from adb.infra.config import get_settings

# Explorers (namespaces de query/coleta) - via lazy loading
_sgs = None
_expectations = None
_ipea = None
_bloomberg = None
_sidra = None


def __getattr__(name):
    """Lazy loading dos explorers."""
    global _sgs, _expectations, _ipea, _bloomberg, _sidra

    if name == "sgs":
        if _sgs is None:
            from adb.providers.bacen.sgs.explorer import SGSExplorer

            _sgs = SGSExplorer()
        return _sgs

    if name == "expectations":
        if _expectations is None:
            from adb.providers.bacen.expectations.explorer import ExpectationsExplorer

            _expectations = ExpectationsExplorer()
        return _expectations

    if name == "ipea":
        if _ipea is None:
            from adb.providers.ipea.explorer import IPEAExplorer

            _ipea = IPEAExplorer()
        return _ipea

    if name == "bloomberg":
        if _bloomberg is None:
            from adb.providers.bloomberg.explorer import BloombergExplorer

            _bloomberg = BloombergExplorer()
        return _bloomberg

    if name == "sidra":
        if _sidra is None:
            from adb.providers.ibge.sidra.explorer import SidraExplorer

            _sidra = SidraExplorer()
        return _sidra

    raise AttributeError(f"module 'adb' has no attribute '{name}'")


def available_sources() -> list[str]:
    """Lista todas as fontes de dados disponiveis."""
    return ["sgs", "expectations", "ipea", "bloomberg", "sidra"]


__all__ = [
    # Explorers
    "sgs",
    "expectations",
    "ipea",
    "bloomberg",
    "sidra",
    # Config
    "get_settings",
    # Helpers
    "available_sources",
]
