"""
Coletor de dados IBGE Sidra.

Orquestra a coleta de series temporais do Sistema IBGE de Recuperacao Automatica (SIDRA).
"""

from pathlib import Path

import pandas as pd

from adb.services.collectors import BaseCollector
from .client import SidraClient
from .indicators import SIDRA_CONFIG


class SidraCollector(BaseCollector):
    """
    Orquestrador de coleta de dados IBGE Sidra.

    Herda template collect() do BaseCollector.
    Implementa _collect_one() para chamar SidraClient.
    """

    _CONFIG = SIDRA_CONFIG
    _TITLE = "IBGE - Sistema SIDRA"
    default_subdir = "ibge/sidra/monthly"

    def __init__(self, data_path: Path | None = None):
        super().__init__(data_path)
        self.client = SidraClient()

    def _subdir_for(self, key: str) -> str:
        frequency = self._CONFIG[key].get("frequency", "monthly")
        return f"ibge/sidra/{frequency}"

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
        subdir = self._subdir_for(key)

        def fetch(start_date: str | None, end_date: str | None) -> pd.DataFrame:
            return self.client.get_data(
                config=config["parameters"],
                start_date=start_date,
                end_date=end_date,
            )

        self._persist(
            fetch_fn=fetch,
            filename=key,
            name=config["name"],
            subdir=subdir,
            frequency=frequency,
            start=start,
            end=end,
            save=save,
            verbose=verbose,
        )

    def _get_frequency_for_file(self, filename: str) -> str:
        config = SIDRA_CONFIG.get(filename, {})
        return config.get("frequency", "monthly")
