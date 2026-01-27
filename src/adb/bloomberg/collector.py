"""
Coletor de dados Bloomberg.

Orquestra a coleta de series temporais do Bloomberg Terminal via xbbg.
"""

from pathlib import Path

import pandas as pd

from adb.core.collectors import BaseCollector
from adb.core.utils import get_config
from .client import BloombergClient
from .indicators import BLOOMBERG_CONFIG


class BloombergCollector(BaseCollector):
    """
    Orquestrador de coleta de dados Bloomberg.

    API publica:
    - collect() - Coleta um ou mais indicadores usando config predefinida
    - consolidate() - Consolida arquivos em DataFrame unico
    - get_status() - Status dos arquivos salvos

    Herda de BaseCollector para logging padronizado e get_status().
    """

    default_subdir = "bloomberg/daily"

    def __init__(self, data_path: Path = None):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho para diretorio data/ (opcional, usa DATA_PATH se None)
        """
        super().__init__(data_path)
        self.client = BloombergClient()

    # =========================================================================
    # Metodo interno de coleta
    # =========================================================================

    def _collect_series(
        self,
        ticker: str,
        field: str,
        filename: str,
        name: str = None,
        frequency: str = "daily",
        subdir: str = None,
        save: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Coleta uma serie temporal Bloomberg.

        Suporta atualizacao incremental: se ja existem dados salvos,
        busca apenas registros novos desde a ultima data.

        Args:
            ticker: Bloomberg ticker (ex: 'MXWD Index')
            field: Bloomberg field (ex: 'PX_LAST')
            filename: Nome do arquivo para salvar (sem extensao)
            name: Nome da serie para logs (default: usa filename)
            frequency: 'daily' (Bloomberg padrao)
            subdir: Subdiretorio dentro de raw/ (default: bloomberg/{frequency})
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            DataFrame com dados coletados
        """
        name = name or filename
        subdir = subdir or f"bloomberg/{frequency}"

        def fetch(start_date: str | None) -> pd.DataFrame:
            return self.client.get_data(
                ticker=ticker,
                field=field,
                name=name,
                start_date=start_date,
            )

        return self._sync(
            fetch_fn=fetch,
            filename=filename,
            name=name,
            subdir=subdir,
            frequency=frequency,
            save=save,
            verbose=verbose,
        )

    # =========================================================================
    # API Publica
    # =========================================================================

    def collect(
        self,
        indicators: list[str] | str = "all",
        save: bool = True,
        verbose: bool = True,
    ) -> None:
        """
        Coleta um ou mais indicadores Bloomberg.

        Args:
            indicators: Indicadores a coletar:
                - 'all': todos de BLOOMBERG_CONFIG
                - lista: ['msci_acwi_pe', 'ibov_points', ...]
                - string: 'msci_acwi_pe' (um unico)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            Dict {indicator_key: DataFrame} com dados coletados
        """
        # Normalizar para lista
        keys = self._normalize_indicators(indicators, BLOOMBERG_CONFIG)

        self._start(
            title="BLOOMBERG - Market Data",
            num_indicators=len(keys),
            verbose=verbose,
        )

        for key in keys:
            config = get_config(BLOOMBERG_CONFIG, key)

            # Bloomberg CONFIG tem 'fields' como lista, pegar primeiro field
            # (cada indicador tem exatamente 1 field por design)
            field = (
                config["fields"][0]
                if isinstance(config["fields"], list)
                else config["fields"]
            )

            self._collect_series(
                ticker=config["ticker"],
                field=field,
                filename=key,
                name=config["name"],
                frequency=config["frequency"],
                save=save,
                verbose=verbose,
            )

        self._end(verbose=verbose)

