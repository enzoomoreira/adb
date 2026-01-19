"""
Coletor de dados IBGE Sidra.
"""

import pandas as pd
from pathlib import Path

from core.collectors import BaseCollector
from core.utils import get_indicator_config
from .client import SidraClient
from .indicators import SIDRA_CONFIG

class SidraCollector(BaseCollector):
    """
    Orquestrador de coleta de dados IBGE Sidra.
    """

    default_subdir = 'ibge/sidra/monthly' # Default padrao

    def __init__(self, data_path: Path = None):
        super().__init__(data_path)
        self.client = SidraClient()

    def collect(
        self,
        indicators: list[str] | str = 'all',
        save: bool = True,
        verbose: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Coleta um ou mais indicadores do IBGE Sidra.
        """
        keys = self._normalize_indicators_list(indicators, SIDRA_CONFIG)

        self._log_collect_start(
            title="IBGE - Sistema SIDRA",
            num_indicators=len(keys),
            subdir=self.default_subdir,
            check_first_run=True,
            verbose=verbose,
        )

        results = {}
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
            df = self._collect_with_sync(
                fetch_fn=fetch,
                filename=key,
                name=config['name'],
                subdir=subdir,
                frequency=config.get('frequency', 'monthly'),
                save=save,
                verbose=verbose,
            )
            
            results[key] = df
            
            if verbose:
                print()

        self._log_collect_end(verbose=verbose)
        return results

    def get_status(self) -> pd.DataFrame:
        """
        Retorna status dos arquivos IBGE Sidra (monthly e quarterly).

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

