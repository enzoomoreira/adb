"""
Coletor de dados Bloomberg.

Orquestra a coleta de series temporais do Bloomberg Terminal via xbbg.
"""

from pathlib import Path

import pandas as pd

from core.collectors import BaseCollector
from core.indicators import get_indicator_config
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
    default_consolidate_subdirs = ["bloomberg/daily"]

    def __init__(self, data_path: Path, check_connection: bool = True):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho para diretorio data/
            check_connection: Se True, valida conexao Bloomberg no init

        Raises:
            RuntimeError: Se Bloomberg nao disponivel e check_connection=True
        """
        super().__init__(data_path)
        self.client = BloombergClient(check_connection=check_connection)

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
                verbose=False,
            )

        return self._collect_with_sync(
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
    ) -> dict[str, pd.DataFrame]:
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
        keys = self._normalize_indicators_list(indicators, BLOOMBERG_CONFIG)

        self._log_collect_start(
            title="BLOOMBERG - Market Data",
            num_indicators=len(keys),
            verbose=verbose,
        )

        results = {}

        for key in keys:
            config = get_indicator_config(BLOOMBERG_CONFIG, key)

            # Bloomberg CONFIG tem 'fields' como lista, pegar primeiro field
            # (cada indicador tem exatamente 1 field por design)
            field = (
                config["fields"][0]
                if isinstance(config["fields"], list)
                else config["fields"]
            )

            df = self._collect_series(
                ticker=config["ticker"],
                field=field,
                filename=key,
                name=config["name"],
                frequency=config["frequency"],
                save=save,
                verbose=verbose,
            )

            results[key] = df

        self._log_collect_end(verbose=verbose)

        return results

    # =========================================================================
    # Consolidacao
    # =========================================================================

    def consolidate(
        self,
        subdir: str = "bloomberg/daily",
        output_filename: str = "bloomberg_daily_consolidated",
        save: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Consolida arquivos Bloomberg.

        Faz join horizontal dos arquivos por indice (data).

        Args:
            subdir: Subdiretorio a consolidar
            output_filename: Nome do arquivo consolidado
            save: Se True, salva em processed/
            verbose: Se True, imprime progresso

        Returns:
            DataFrame consolidado
        """
        self._log_consolidate_start(
            title="CONSOLIDANDO DADOS BLOOMBERG",
            subdir=subdir,
            verbose=verbose,
        )

        df = self.data_manager.consolidate(
            subdir=subdir,
            output_filename=output_filename,
            save=save,
            verbose=verbose,
        )

        if verbose:
            if not df.empty:
                print(
                    f"\nConsolidado: {len(df):,} registros, {len(df.columns)} colunas"
                )
            print("Consolidacao concluida!")

        return df
