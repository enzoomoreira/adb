"""
Explorer IPEA - Interface pythonica para query de series IPEADATA.

Uso:
    from adb.core.data import ipea

    df = ipea.read('caged_saldo')
    df = ipea.read('caged_saldo', start='2020')
    print(ipea.available())
"""

from adb.core.data.explorers import BaseExplorer
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
        from adb.ipea.collector import IPEACollector
        return IPEACollector
