"""
Explorer IPEA - Interface pythonica para query de series IPEADATA.

Uso:
    from adb.core.data import ipea

    df = ipea.read('caged_saldo')
    df = ipea.read('caged_saldo', start='2020')
    print(ipea.available())
"""

import pandas as pd

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

    def _fetch_one(
        self, indicator: str, start: str | None, end: str | None
    ) -> pd.DataFrame:
        from adb.providers.ipea.client import IPEAClient

        config = self._CONFIG[indicator]
        client = IPEAClient()
        return client.get_data(
            code=config["code"],
            name=config["name"],
            start_date=start,
            end_date=end,
        )
