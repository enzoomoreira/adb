"""adb - Acesso unificado a dados economicos brasileiros.

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

import importlib

from adb.infra.config import get_settings

_EXPLORER_REGISTRY: dict[str, tuple[str, str]] = {
    "sgs": ("adb.providers.bacen.sgs.explorer", "SGSExplorer"),
    "expectations": (
        "adb.providers.bacen.expectations.explorer",
        "ExpectationsExplorer",
    ),
    "ipea": ("adb.providers.ipea.explorer", "IPEAExplorer"),
    "sidra": ("adb.providers.ibge.sidra.explorer", "SidraExplorer"),
    "bloomberg": ("adb.providers.bloomberg.explorer", "BloombergExplorer"),
}

_instances: dict[str, object] = {}


def __getattr__(name: str):
    """Lazy loading dos explorers via registry."""
    if name in _EXPLORER_REGISTRY:
        if name not in _instances:
            module_path, class_name = _EXPLORER_REGISTRY[name]
            mod = importlib.import_module(module_path)
            _instances[name] = getattr(mod, class_name)()
        return _instances[name]
    raise AttributeError(f"module 'adb' has no attribute '{name}'")


def available_sources() -> list[str]:
    """Lista todas as fontes de dados disponiveis."""
    return list(_EXPLORER_REGISTRY.keys())


__all__ = [
    "sgs",
    "expectations",
    "ipea",
    "bloomberg",
    "sidra",
    "get_settings",
    "available_sources",
]
