"""
Coletor de expectativas do BCB (Relatorio Focus).

Orquestra a coleta de dados de expectativas com flexibilidade de parametros.
"""

from pathlib import Path

import pandas as pd

from adb.services.collectors import BaseCollector
from .client import ExpectationsClient
from .indicators import EXPECTATIONS_CONFIG


class ExpectationsCollector(BaseCollector):
    """
    Orquestrador de coleta de expectativas do BCB (Relatorio Focus).

    Herda template collect() do BaseCollector.
    Implementa _collect_one() para chamar ExpectationsClient.
    """

    _CONFIG = EXPECTATIONS_CONFIG
    _TITLE = "BACEN - Expectativas (Relatorio Focus)"
    default_subdir = "bacen/expectations"

    def __init__(self, data_path: Path | None = None):
        super().__init__(data_path)
        self.client = ExpectationsClient()

    def _collect_one(
        self,
        key: str,
        config: dict,
        start: str | None,
        end: str | None,
        save: bool,
        verbose: bool,
    ) -> None:
        log_name = config.get("indicator") or key

        def fetch(start_date: str | None, end_date: str | None) -> pd.DataFrame:
            return self.client.query(
                endpoint_key=config["endpoint"],
                indicator=config.get("indicator"),
                start_date=start_date,
                end_date=end_date,
            )

        self._persist(
            fetch_fn=fetch,
            filename=key,
            name=log_name,
            subdir=self.default_subdir,
            frequency="daily",
            start=start,
            end=end,
            save=save,
            verbose=verbose,
        )

    def _get_frequency_for_file(self, filename: str) -> str | None:
        if filename in EXPECTATIONS_CONFIG:
            return "daily"
        return None
