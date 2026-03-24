"""
Registry interno de collectors.
"""

import importlib

_COLLECTOR_MAP = {
    "sgs": ("bacen.sgs.collector", "SGSCollector"),
    "expectations": ("bacen.expectations.collector", "ExpectationsCollector"),
    "ipea": ("ipea.collector", "IPEACollector"),
    "bloomberg": ("bloomberg.collector", "BloombergCollector"),
    "sidra": ("ibge.sidra.collector", "SidraCollector"),
}


def _get_collector(name: str):
    """Importa e retorna classe do collector (uso interno)."""
    if name not in _COLLECTOR_MAP:
        available = ", ".join(_COLLECTOR_MAP.keys())
        raise ValueError(f"Collector '{name}' nao encontrado. Disponiveis: {available}")

    module_path, class_name = _COLLECTOR_MAP[name]
    module = importlib.import_module(module_path)
    return getattr(module, class_name)
