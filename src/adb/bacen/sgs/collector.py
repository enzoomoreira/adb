"""
Coletor de dados SGS do BCB.

Orquestra a coleta de series temporais com flexibilidade de parametros.
"""

from pathlib import Path
import pandas as pd

from adb.core.collectors import BaseCollector
from adb.core.utils import get_indicator_config
from .client import SGSClient
from .indicators import SGS_CONFIG


class SGSCollector(BaseCollector):
    """
    Orquestrador de coleta de dados SGS.

    API publica:
    - collect() - Coleta um ou mais indicadores usando config predefinida
    - consolidate() - Consolida arquivos em DataFrame unico
    - get_status() - Status dos arquivos salvos

    Herda de BaseCollector para logging padronizado e get_status().
    """

    default_subdir = 'bacen/sgs/daily'

    def __init__(self, data_path: Path = None):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho para diretorio data/ (opcional, usa DATA_PATH se None)
        """
        super().__init__(data_path)
        self.client = SGSClient()

    # =========================================================================
    # Metodo interno de coleta
    # =========================================================================

    def _collect_series(
        self,
        code: int,
        filename: str,
        name: str = None,
        frequency: str = 'daily',
        subdir: str = None,
        save: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Coleta uma serie temporal com controle total.

        Suporta atualizacao incremental: se ja existem dados salvos,
        busca apenas registros novos desde a ultima data.

        Args:
            code: Codigo SGS do indicador
            filename: Nome do arquivo para salvar (sem extensao)
            name: Nome da serie (default: usa filename)
            frequency: 'daily' ou 'monthly'
            subdir: Subdiretorio dentro de raw/ (default: sgs/{frequency})
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            DataFrame com dados coletados
        """
        if name is None:
            name = filename
        if subdir is None:
            subdir = f"bacen/sgs/{frequency}"

        def fetch(start_date: str | None) -> pd.DataFrame:
            return self.client.get_data(
                code=code,
                name=name,
                frequency=frequency,
                start_date=start_date,
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
        indicators: list[str] | str = 'all',
        save: bool = True,
        verbose: bool = True,
    ) -> None:
        """
        Coleta um ou mais indicadores.

        Args:
            indicators: Indicadores a coletar:
                - 'all': todos de SGS_CONFIG
                - lista: ['selic', 'cdi', ...]
                - string: 'selic' (um unico)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            Dict {indicator_key: DataFrame} com dados coletados
        """
        # Normalizar entrada
        keys = self._normalize_indicators_list(indicators, SGS_CONFIG)

        self._log_collect_start(
            title="BACEN - Sistema Gerenciador de Series",
            num_indicators=len(keys),
            subdir='bacen/sgs/daily',
            check_first_run=True,
            verbose=verbose,
        )

        for key in keys:
            config = get_indicator_config(SGS_CONFIG, key)
            subdir = f"bacen/sgs/{config['frequency']}"

            self._collect_series(
                code=config['code'],
                filename=key,
                name=config['name'],
                frequency=config['frequency'],
                subdir=subdir,
                save=save,
                verbose=verbose,
            )

        self._log_collect_end(verbose=verbose)

    # =========================================================================

    def get_status(self) -> pd.DataFrame:
        """
        Retorna status dos arquivos SGS (daily e monthly).

        Returns:
            DataFrame com status de cada arquivo
        """
        dfs = []
        subdirs = ['bacen/sgs/daily', 'bacen/sgs/monthly']
        for subdir in subdirs:
            df = super().get_status(subdir)
            if not df.empty:
                dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        return pd.concat(dfs, ignore_index=True)

