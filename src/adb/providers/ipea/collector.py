"""
Coletor de dados IPEA.

Orquestra a coleta de series temporais do IPEADATA.
"""

from pathlib import Path

import pandas as pd

from adb.services.collectors import BaseCollector
from .client import IPEAClient
from .indicators import IPEA_CONFIG


class IPEACollector(BaseCollector):
    """
    Orquestrador de coleta de dados IPEA (IPEADATA).

    Herda template collect() do BaseCollector.
    Implementa _collect_one() para chamar IPEAClient.
    """

    _CONFIG = IPEA_CONFIG
    _TITLE = "IPEA - Instituto de Pesquisa Economica Aplicada"
    default_subdir = "ipea/monthly"

    def __init__(self, data_path: Path | None = None):
        super().__init__(data_path)
        self.client = IPEAClient()

    def _collect_one(
        self,
        key: str,
        config: dict,
        start: str | None,
        end: str | None,
        save: bool,
        verbose: bool,
    ) -> None:
        frequency = self._get_frequency_for_file(key)
        subdir = f"ipea/{frequency}"

        def fetch(start_date: str | None, end_date: str | None) -> pd.DataFrame:
            return self.client.get_data(
                code=config["code"],
                name=config["name"],
                start_date=start_date,
                end_date=end_date,
            )

        # Para quarterly, usar monthly (DataManager pula para proximo mes)
        effective_freq = "monthly" if frequency == "quarterly" else frequency

        self._persist(
            fetch_fn=fetch,
            filename=key,
            name=config["name"],
            subdir=subdir,
            frequency=effective_freq,
            start=start,
            end=end,
            save=save,
            verbose=verbose,
        )

    def _get_frequency_for_file(self, filename: str) -> str:
        config = IPEA_CONFIG.get(filename, {})
        return config.get("frequency", "monthly")
