"""
Explorer IPEA - Interface pythonica para query de series IPEADATA.

Uso:
    from adb.core.data import ipea

    df = ipea.read('caged_saldo')
    df = ipea.read('caged_saldo', start='2020')
    print(ipea.available())
"""

from adb.domain.explorers import BaseExplorer
from .indicators import IPEA_CONFIG


class IPEAExplorer(BaseExplorer):
    """
    Explorer para dados IPEA.

    Fornece interface pythonica para leitura de series temporais
    agregadas do IPEADATA.
    """

    _CONFIG = IPEA_CONFIG
    _SUBDIR = "ipea/monthly"

    @property
    def _COLLECTOR_CLASS(self):
        """Retorna a classe do coletor associado."""
        from adb.providers.ipea.collector import IPEACollector
        return IPEACollector
