"""
Explorer SGS - Interface pythonica para query de series temporais BCB.

Uso:
    from adb.core.data import sgs

    df = sgs.read('selic')
    df = sgs.read('selic', start='2020', end='2023')
    df = sgs.read('selic', 'cdi', 'dolar_ptax')
    print(sgs.available())
"""

from typing import List
import pandas as pd

from adb.core.utils import parse_date
from .indicators import SGS_CONFIG


class SGSExplorer:
    """
    Explorer para dados SGS.

    Fornece interface pythonica para leitura de series temporais
    do Sistema Gerenciador de Series Temporais do BCB.
    """

    def __init__(self, query_engine=None):
        """
        Inicializa o explorer SGS.

        Args:
            query_engine: QueryEngine customizado (opcional, cria novo se None)
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
        Le series temporais SGS.

        Args:
            *indicators: Nomes dos indicadores (ex: 'selic', 'cdi')
            start: Data inicial (formatos: '2020', '2020-01', '2020-01-01')
            end: Data final (mesmos formatos)
            columns: Colunas especificas (default: todas)

        Returns:
            DataFrame com series temporais
            - Um indicador: DatetimeIndex + coluna 'value'
            - Multiplos: DatetimeIndex + coluna por indicador

        Examples:
            >>> sgs.read('selic')
            >>> sgs.read('selic', start='2020')
            >>> sgs.read('selic', 'cdi', start='2020', end='2023')
            >>> sgs.read()  # Todos os indicadores
        """
        if not indicators:
            indicators = tuple(SGS_CONFIG.keys())

        # Validar indicadores
        for ind in indicators:
            if ind not in SGS_CONFIG:
                available = ', '.join(SGS_CONFIG.keys())
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
            config = SGS_CONFIG[indicators[0]]
            subdir = f"bacen/sgs/{config['frequency']}"
            return self._qe.read(indicators[0], subdir, columns=columns, where=where)

        # Multiplos indicadores: join por data
        dfs = []
        for ind in indicators:
            config = SGS_CONFIG[ind]
            subdir = f"bacen/sgs/{config['frequency']}"
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
            frequency: Filtrar por frequencia ('daily', 'monthly')

        Returns:
            Lista de nomes de indicadores

        Examples:
            >>> sgs.available()
            ['ibc_br_bruto', 'ibc_br_dessaz', 'igp_m', 'selic', ...]
            >>> sgs.available(frequency='daily')
            ['selic', 'dolar_ptax', 'euro_ptax', 'cdi']
        """
        if frequency:
            return [k for k, v in SGS_CONFIG.items() if v.get('frequency') == frequency]
        return list(SGS_CONFIG.keys())

    def info(self, indicator: str = None) -> dict:
        """
        Retorna informacoes sobre indicador(es).

        Args:
            indicator: Nome do indicador. None = todos.

        Returns:
            Dict com informacoes do(s) indicador(es)

        Examples:
            >>> sgs.info('selic')
            {'code': 432, 'name': 'Meta Selic', 'frequency': 'daily', ...}
            >>> sgs.info()  # Retorna todos
        """
        if indicator:
            if indicator not in SGS_CONFIG:
                raise KeyError(f"Indicador '{indicator}' nao encontrado")
            return SGS_CONFIG[indicator].copy()
        return SGS_CONFIG.copy()

    def collect(
        self,
        indicators: list[str] | str = 'all',
        save: bool = True,
        verbose: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Coleta dados SGS do BCB.

        Args:
            indicators: 'all', lista, ou string com indicador(es)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            Dict {indicator_key: DataFrame}

        Examples:
            >>> sgs.collect()
            >>> sgs.collect('selic')
        """
        from adb.bacen.sgs.collector import SGSCollector
        collector = SGSCollector()
        return collector.collect(indicators=indicators, save=save, verbose=verbose)

    def get_status(self) -> pd.DataFrame:
        """Retorna status dos arquivos SGS salvos."""
        from adb.bacen.sgs.collector import SGSCollector
        collector = SGSCollector()
        return collector.get_status()
