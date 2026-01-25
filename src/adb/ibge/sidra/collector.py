"""
Coletor de dados IBGE Sidra.

Orquestra a coleta de series temporais do Sistema IBGE de Recuperacao Automatica (SIDRA).
"""

import pandas as pd
from pathlib import Path

from adb.core.collectors import BaseCollector
from adb.core.utils import get_indicator_config
from .client import SidraClient
from .indicators import SIDRA_CONFIG

class SidraCollector(BaseCollector):
    """
    Orquestrador de coleta de dados IBGE Sidra.

    API publica:
    - collect() - Coleta um ou mais indicadores usando config predefinida
    - get_status() - Status dos arquivos salvos

    Herda de BaseCollector para logging padronizado e get_status().
    """

    default_subdir = 'ibge/sidra/monthly'

    def __init__(self, data_path: Path = None):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho para diretorio data/ (opcional, usa DATA_PATH se None)
        """
        super().__init__(data_path)
        self.client = SidraClient()

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
        Coleta um ou mais indicadores do IBGE Sidra.

        Args:
            indicators: Indicadores a coletar:
                - 'all': todos de SIDRA_CONFIG
                - lista: ['ipca', 'pib', ...]
                - string: 'ipca' (um unico)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso
        """
        keys = self._normalize_indicators_list(indicators, SIDRA_CONFIG)

        self._log_collect_start(
            title="IBGE - Sistema SIDRA",
            num_indicators=len(keys),
            subdir=self.default_subdir,
            check_first_run=True,
            verbose=verbose,
        )

        for key in keys:
            config = get_indicator_config(SIDRA_CONFIG, key)
            # Define subdiretorio baseado na frequencia, similar ao SGS
            subdir = f"ibge/sidra/{config.get('frequency', 'monthly')}"

            # Logica de fetch
            def fetch(start_date: str | None) -> pd.DataFrame:
                return self.client.get_data(
                    config=config['parameters'],
                    start_date=start_date,
                    verbose=False
                )
            
            # Usa o metodo _collect_with_sync do BaseCollector que ja trata
            # verificacao de existencia, delta update e salvamento.
            self._collect_with_sync(
                fetch_fn=fetch,
                filename=key,
                name=config['name'],
                subdir=subdir,
                frequency=config.get('frequency', 'monthly'),
                save=save,
                verbose=verbose,
            )
            
            if verbose:
                print()

        self._log_collect_end(verbose=verbose)

    def get_status(self) -> pd.DataFrame:
        """
        Retorna status dos arquivos IBGE Sidra.
        
        Agrega status dos diretorios monthly e quarterly.

        Returns:
            DataFrame com status de cada arquivo
        """
        dfs = []
        subdirs = ['ibge/sidra/monthly', 'ibge/sidra/quarterly']
        for subdir in subdirs:
            df = super().get_status(subdir)
            if not df.empty:
                dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        return pd.concat(dfs, ignore_index=True)

