"""
Coletor de dados Bloomberg.

Orquestra a coleta de series temporais do Bloomberg Terminal via xbbg.
"""

from pathlib import Path

import pandas as pd

from adb.services.collectors import BaseCollector
from .client import BloombergClient
from .indicators import BLOOMBERG_CONFIG


class BloombergCollector(BaseCollector):
    """
    Orquestrador de coleta de dados Bloomberg.

    Herda template collect() do BaseCollector.
    Implementa _collect_one() para chamar BloombergClient.
    """

    _CONFIG = BLOOMBERG_CONFIG
    _TITLE = "BLOOMBERG - Market Data"
    default_subdir = "bloomberg/daily"

    def __init__(self, data_path: Path | None = None):
        super().__init__(data_path)
        self.client = BloombergClient()

    def _subdir_for(self, key: str) -> str:
        frequency = self._CONFIG[key].get("frequency", "daily")
        return f"bloomberg/{frequency}"

    def _collect_one(self, key: str, config: dict, save: bool, verbose: bool) -> None:
        frequency = self._get_frequency_for_file(key)
        subdir = self._subdir_for(key)

        field = (
            config["fields"][0]
            if isinstance(config["fields"], list)
            else config["fields"]
        )

        def fetch(start_date: str | None) -> pd.DataFrame:
            return self.client.get_data(
                ticker=config["ticker"],
                field=field,
                name=config["name"],
                start_date=start_date,
            )

        self._sync(
            fetch_fn=fetch,
            filename=key,
            name=config["name"],
            subdir=subdir,
            frequency=frequency,
            save=save,
            verbose=verbose,
        )

    def _get_frequency_for_file(self, filename: str) -> str:
        config = BLOOMBERG_CONFIG.get(filename, {})
        return config.get("frequency", "daily")
