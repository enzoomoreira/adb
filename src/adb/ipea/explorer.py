"""
Explorer IPEA - Interface pythonica para query de series IPEADATA.

Uso:
    from adb.core.data import ipea

    df = ipea.read('caged_saldo')
    df = ipea.read('caged_saldo', start='2020')
    print(ipea.available())
"""

from typing import List
import pandas as pd

from adb.core.utils import parse_date
from .indicators import IPEA_CONFIG


class IPEAExplorer:
    """
    Explorer para dados IPEA.

    Fornece interface pythonica para leitura de series temporais
    agregadas do IPEADATA.
    """

    _SUBDIR = "ipea/monthly"

    def __init__(self, query_engine=None):
        """
        Inicializa o explorer IPEA.

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
        Le series temporais IPEA.

        Args:
            *indicators: Nomes dos indicadores (ex: 'caged_saldo', 'taxa_desemprego')
            start: Data inicial (formatos: '2020', '2020-01', '2020-01-01')
            end: Data final (mesmos formatos)
            columns: Colunas especificas (default: todas)

        Returns:
            DataFrame com series temporais
            - Um indicador: DatetimeIndex + coluna 'value'
            - Multiplos: DatetimeIndex + coluna por indicador

        Examples:
            >>> ipea.read('caged_saldo')
            >>> ipea.read('caged_saldo', start='2020')
            >>> ipea.read('caged_saldo', 'taxa_desemprego')
            >>> ipea.read()  # Todos os indicadores
        """
        if not indicators:
            indicators = tuple(IPEA_CONFIG.keys())

        # Validar indicadores
        for ind in indicators:
            if ind not in IPEA_CONFIG:
                available = ', '.join(IPEA_CONFIG.keys())
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

    def available(self, source: str = None) -> list[str]:
        """
        Lista indicadores disponiveis.

        Args:
            source: Filtrar por fonte (ex: 'MTE/CAGED', 'IBGE/PNAD')

        Returns:
            Lista de nomes de indicadores

        Examples:
            >>> ipea.available()
            ['caged_saldo', 'caged_admissoes', 'caged_desligamentos', 'taxa_desemprego']
        """
        if source:
            return [k for k, v in IPEA_CONFIG.items() if v.get('source') == source]
        return list(IPEA_CONFIG.keys())

    def info(self, indicator: str = None) -> dict:
        """
        Retorna informacoes sobre indicador(es).

        Args:
            indicator: Nome do indicador. None = todos.

        Returns:
            Dict com informacoes do(s) indicador(es)

        Examples:
            >>> ipea.info('caged_saldo')
            {'code': 'CAGED12_SALDON12', 'name': 'Saldo do Novo CAGED', ...}
        """
        if indicator:
            if indicator not in IPEA_CONFIG:
                raise KeyError(f"Indicador '{indicator}' nao encontrado")
            return IPEA_CONFIG[indicator].copy()
        return IPEA_CONFIG.copy()

    def collect(
        self,
        indicators: list[str] | str = "all",
        save: bool = True,
        verbose: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Coleta series temporais do IPEADATA.

        Args:
            indicators: 'all', lista, ou string com indicador(es)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            Dict {indicator_key: DataFrame}

        Examples:
            >>> ipea.collect()
            >>> ipea.collect('caged_saldo')
        """
        from adb.ipea.collector import IPEACollector
        collector = IPEACollector()
        return collector.collect(indicators=indicators, save=save, verbose=verbose)

    def get_status(self) -> pd.DataFrame:
        """Retorna status dos arquivos IPEA salvos."""
        from adb.ipea.collector import IPEACollector
        collector = IPEACollector()
        return collector.get_status()
