"""
Explorer Bloomberg - Interface pythonica para query de dados de mercado.

Uso:
    from adb.core.data import bloomberg

    df = bloomberg.read('ibov_points')
    df = bloomberg.read('ibov_points', start='2020')
    print(bloomberg.available())

Nota: Requer Bloomberg Terminal para coleta, mas leitura funciona offline.
"""

import pandas as pd

from adb.domain.explorers import BaseExplorer
from .indicators import BLOOMBERG_CONFIG


class BloombergExplorer(BaseExplorer):
    """
    Explorer para dados Bloomberg.

    Fornece interface pythonica para leitura de series temporais
    de mercado coletadas via Bloomberg Terminal.
    """

    _CONFIG = BLOOMBERG_CONFIG
    _SUBDIR = "bloomberg/daily"

    @property
    def _COLLECTOR_CLASS(self):
        """Retorna a classe do coletor associado."""
        from adb.providers.bloomberg.collector import BloombergCollector

        return BloombergCollector

    # =========================================================================
    # Metodos auxiliares
    # =========================================================================

    def _subdir(self, indicator: str) -> str:
        """Bloomberg tem subdir dinamico baseado em frequency."""
        return f"bloomberg/{self._CONFIG[indicator]['frequency']}"

    def _fetch_one(
        self, indicator: str, start: str | None, end: str | None
    ) -> pd.DataFrame:
        from adb.providers.bloomberg.client import BloombergClient

        config = self._CONFIG[indicator]
        client = BloombergClient()
        return client.get_data(
            ticker=config["ticker"],
            field=config["fields"][0],
            name=config["name"],
            start_date=start,
            end_date=end,
        )
