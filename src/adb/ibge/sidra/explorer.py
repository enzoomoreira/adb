"""
Explorer SIDRA - Interface pythonica para query de series do IBGE.

Uso:
    from adb.core.data import sidra
    
    df = sidra.read('ipca')
    df = sidra.read('ipca', start='2020')
    print(sidra.available())
"""

from typing import List
import pandas as pd

from adb.core.utils import parse_date
from .indicators import SIDRA_CONFIG


class SidraExplorer:
    """
    Explorer para dados IBGE Sidra.
    
    Fornece interface pythonica para leitura de series temporais
    do Sistema IBGE de Recuperacao Automatica (SIDRA).
    """

    def __init__(self, query_engine=None):
        """
        Inicializa o explorer SIDRA.
        
        Args:
            query_engine: QueryEngine customizado (opcional)
        """
        from adb.core.data import QueryEngine
        self._qe = query_engine or QueryEngine()

    def read(
        self,
        *indicators: str,
        start: str = None,
        end: str = None,
        columns: List[str] = None,
    ) -> pd.DataFrame:
        """
        Le series temporais do IBGE Sidra.
        
        Args:
            *indicators: Nomes dos indicadores (ex: 'ipca')
            start: Data inicial (formatos: '2020', '2020-01', '2020-01-01')
            end: Data final (mesmos formatos)
            columns: Colunas especificas (default: todas)
            
        Returns:
            DataFrame com series temporais
        """
        if not indicators:
            indicators = tuple(SIDRA_CONFIG.keys())

        # Validar indicadores
        for ind in indicators:
            if ind not in SIDRA_CONFIG:
                available = ', '.join(SIDRA_CONFIG.keys())
                raise KeyError(f"Indicador '{ind}' nao encontrado. Disponiveis: {available}")

        # Construir WHERE
        where_clauses = []
        if start:
            where_clauses.append(f"date >= '{parse_date(start)}'")
        if end:
            where_clauses.append(f"date <= '{parse_date(end)}'")
        where = " AND ".join(where_clauses) if where_clauses else None

        # Um indicador: retorna direto
        if len(indicators) == 1:
            config = SIDRA_CONFIG[indicators[0]]
            subdir = f"ibge/sidra/{config.get('frequency', 'monthly')}"
            return self._qe.read(indicators[0], subdir, columns=columns, where=where)

        # Multiplos indicadores: join por data
        dfs = []
        for ind in indicators:
            config = SIDRA_CONFIG[ind]
            subdir = f"ibge/sidra/{config.get('frequency', 'monthly')}"
            df = self._qe.read(ind, subdir, columns=['value'], where=where)
            if not df.empty:
                df = df.rename(columns={'value': ind})
                dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        result = dfs[0]
        for df in dfs[1:]:
            result = result.join(df, how='outer')

        return result.sort_index()

    def available(self, frequency: str = None) -> list[str]:
        """
        Lista indicadores disponiveis.
        
        Args:
            frequency: Filtrar por frequencia
            
        Returns:
            Lista de nomes de indicadores
        """
        if frequency:
            return [k for k, v in SIDRA_CONFIG.items() if v.get('frequency') == frequency]
        return list(SIDRA_CONFIG.keys())

    def info(self, indicator: str = None) -> dict:
        """
        Retorna informacoes sobre indicador(es).
        """
        if indicator:
            if indicator not in SIDRA_CONFIG:
                raise KeyError(f"Indicador '{indicator}' nao encontrado")
            return SIDRA_CONFIG[indicator].copy()
        return SIDRA_CONFIG.copy()

    def collect(
        self,
        indicators: list[str] | str = 'all',
        save: bool = True,
        verbose: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Coleta series do IBGE Sidra.

        Args:
            indicators: 'all', lista, ou string com indicador(es)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            Dict {indicator_key: DataFrame}

        Examples:
            >>> sidra.collect()
            >>> sidra.collect('ipca')
        """
        from adb.ibge.sidra.collector import SidraCollector
        collector = SidraCollector()
        return collector.collect(indicators=indicators, save=save, verbose=verbose)

    def get_status(self) -> pd.DataFrame:
        """Retorna status dos arquivos Sidra salvos."""
        from adb.ibge.sidra.collector import SidraCollector
        collector = SidraCollector()
        return collector.get_status()
