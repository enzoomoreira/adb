"""
Explorer Expectations - Interface pythonica para query de expectativas Focus.

Uso:
    from adb.core.data import expectations

    df = expectations.read('ipca_anual')
    df = expectations.read('ipca_anual', start='2023')
    print(expectations.available())
"""

import pandas as pd

from adb.core.data.explorers import BaseExplorer
from .indicators import EXPECTATIONS_CONFIG


class ExpectationsExplorer(BaseExplorer):
    """
    Explorer para dados de Expectativas do BCB (Relatorio Focus).

    Fornece interface pythonica para leitura de expectativas
    de mercado do Banco Central do Brasil.
    """

    _CONFIG = EXPECTATIONS_CONFIG
    _SUBDIR = "bacen/expectations"
    _DATE_COLUMN = "Data"  # Expectations usa "Data" ao invés de "date"

    @property
    def _COLLECTOR_CLASS(self):
        from adb.bacen.expectations.collector import ExpectationsCollector
        return ExpectationsCollector

    def _join_multiple(self, dfs: list, indicators: tuple) -> pd.DataFrame:
        """
        Override: Expectations concatena ao invés de join.
        
        Cada indicador pode ter estrutura diferente, entao concatenamos
        com uma coluna 'indicator' para identificar.
        """
        if not dfs:
            return pd.DataFrame()

        for df, ind in zip(dfs, indicators):
            df['indicator'] = ind

        return pd.concat(dfs, ignore_index=True)

    def collect(
        self,
        indicators: list[str] | str = 'all',
        start_date: str = None,
        limit: int = None,
        save: bool = True,
        verbose: bool = True,
    ) -> None:
        """
        Coleta expectativas do Relatorio Focus (BCB).

        Args:
            indicators: 'all', lista, ou string com indicador(es)
            start_date: Data inicial (formato 'YYYY-MM-DD')
            limit: Limite de registros
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso
        """
        collector = self._COLLECTOR_CLASS()
        collector.collect(
            indicators=indicators, 
            start_date=start_date, 
            limit=limit,
            save=save, 
            verbose=verbose
        )
