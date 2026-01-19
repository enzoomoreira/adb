"""
Explorer Bloomberg - Interface pythonica para query de dados de mercado.

Uso:
    from adb.core.data import bloomberg

    df = bloomberg.read('ibov_points')
    df = bloomberg.read('ibov_points', start='2020')
    print(bloomberg.available())

Nota: Requer Bloomberg Terminal para coleta, mas leitura funciona offline.
"""

from typing import List
import pandas as pd

from adb.core.utils import parse_date
from .indicators import BLOOMBERG_CONFIG


class BloombergExplorer:
    """
    Explorer para dados Bloomberg.

    Fornece interface pythonica para leitura de series temporais
    de mercado coletadas via Bloomberg Terminal.
    """

    _SUBDIR = "bloomberg/daily"

    def __init__(self, query_engine=None):
        """
        Inicializa o explorer Bloomberg.

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
        Le series temporais Bloomberg.

        Args:
            *indicators: Nomes dos indicadores (ex: 'ibov_points', 'brent')
            start: Data inicial (formatos: '2020', '2020-01', '2020-01-01')
            end: Data final (mesmos formatos)
            columns: Colunas especificas (default: todas)

        Returns:
            DataFrame com series temporais
            - Um indicador: DatetimeIndex + coluna 'value'
            - Multiplos: DatetimeIndex + coluna por indicador

        Examples:
            >>> bloomberg.read('ibov_points')
            >>> bloomberg.read('ibov_points', start='2020')
            >>> bloomberg.read('ibov_points', 'brent')
        """
        if not indicators:
            raise ValueError("Pelo menos um indicador deve ser especificado")

        # Validar indicadores
        for ind in indicators:
            if ind not in BLOOMBERG_CONFIG:
                available = ', '.join(BLOOMBERG_CONFIG.keys())
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
            return self._qe.read(indicators[0], self._SUBDIR, columns=columns, where=where)

        # Multiplos indicadores: join por data
        dfs = []
        for ind in indicators:
            df = self._qe.read(ind, self._SUBDIR, columns=['value'], where=where)
            if not df.empty:
                df = df.rename(columns={'value': ind})
                dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        result = dfs[0]
        for df in dfs[1:]:
            result = result.join(df, how='outer')

        return result.sort_index()

    def available(self, category: str = None) -> list[str]:
        """
        Lista indicadores disponiveis.

        Args:
            category: Filtrar por categoria (ex: 'global_equities', 'commodities')

        Returns:
            Lista de nomes de indicadores

        Examples:
            >>> bloomberg.available()
            ['msci_acwi_mktcap', 'ibov_points', 'brent', ...]
            >>> bloomberg.available(category='commodities')
            ['brent', 'iron_ore', 'gold']
        """
        if category:
            return [k for k, v in BLOOMBERG_CONFIG.items() if v.get('category') == category]
        return list(BLOOMBERG_CONFIG.keys())

    def info(self, indicator: str = None) -> dict:
        """
        Retorna informacoes sobre indicador(es).

        Args:
            indicator: Nome do indicador. None = todos.

        Returns:
            Dict com informacoes do(s) indicador(es)

        Examples:
            >>> bloomberg.info('ibov_points')
            {'ticker': 'IBOV Index', 'fields': ['PX_LAST'], ...}
        """
        if indicator:
            if indicator not in BLOOMBERG_CONFIG:
                raise KeyError(f"Indicador '{indicator}' nao encontrado")
            return BLOOMBERG_CONFIG[indicator].copy()
        return BLOOMBERG_CONFIG.copy()

    def collect(
        self,
        indicators: list[str] | str = "all",
        save: bool = True,
        verbose: bool = True,
        check_connection: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Coleta dados de mercado via Bloomberg Terminal.

        Args:
            indicators: 'all', lista, ou string com indicador(es)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso
            check_connection: Se True, valida conexao Bloomberg

        Returns:
            Dict {indicator_key: DataFrame}

        Raises:
            RuntimeError: Se Bloomberg nao disponivel e check_connection=True

        Examples:
            >>> bloomberg.collect()
            >>> bloomberg.collect('ibov_points', check_connection=False)
        """
        from adb.bloomberg.collector import BloombergCollector
        collector = BloombergCollector(check_connection=check_connection)
        return collector.collect(indicators=indicators, save=save, verbose=verbose)

    def get_status(self) -> pd.DataFrame:
        """Retorna status dos arquivos Bloomberg salvos."""
        from adb.bloomberg.collector import BloombergCollector
        collector = BloombergCollector(check_connection=False)
        return collector.get_status()
