"""
Explorer Expectations - Interface pythonica para query de expectativas Focus.

Uso:
    from core.data import expectations

    df = expectations.read('ipca_anual')
    df = expectations.read('ipca_anual', start='2023')
    print(expectations.available())
"""

from typing import List
import pandas as pd

from core.utils import parse_date
from .indicators import EXPECTATIONS_CONFIG


class ExpectationsExplorer:
    """
    Explorer para dados de Expectativas do BCB (Relatorio Focus).

    Fornece interface pythonica para leitura de expectativas
    de mercado do Banco Central do Brasil.
    """

    _SUBDIR = "bacen/expectations"

    def __init__(self, query_engine=None):
        """
        Inicializa o explorer Expectations.

        Args:
            query_engine: QueryEngine customizado (opcional, cria novo se None)
        """
        from core.data import QueryEngine
        self._qe = query_engine or QueryEngine()

    def read(
        self,
        *indicators: str,
        start: str = None,
        end: str = None,
        columns: List[str] = None,
    ) -> pd.DataFrame:
        """
        Le dados de expectativas.

        Args:
            *indicators: Nomes dos indicadores (ex: 'ipca_anual', 'selic')
            start: Data inicial (formatos: '2020', '2020-01', '2020-01-01')
            end: Data final (mesmos formatos)
            columns: Colunas especificas (default: todas)

        Returns:
            DataFrame com expectativas
            - Um indicador: DataFrame completo
            - Multiplos: DataFrame concatenado com coluna 'indicator'

        Examples:
            >>> expectations.read('ipca_anual')
            >>> expectations.read('ipca_anual', start='2023')
            >>> expectations.read('ipca_anual', 'pib_anual')
            >>> expectations.read()  # Todos os indicadores
        """
        if not indicators:
            indicators = tuple(EXPECTATIONS_CONFIG.keys())

        # Validar indicadores
        for ind in indicators:
            if ind not in EXPECTATIONS_CONFIG:
                available = ', '.join(EXPECTATIONS_CONFIG.keys())
                raise KeyError(f"Indicador '{ind}' nao encontrado. Disponiveis: {available}")

        # Construir WHERE
        where_clauses = []
        if start:
            where_clauses.append(f"Data >= '{parse_date(start)}'")
        if end:
            where_clauses.append(f"Data <= '{parse_date(end)}'")
        where = " AND ".join(where_clauses) if where_clauses else None

        # Um indicador: retorna direto
        if len(indicators) == 1:
            return self._qe.read(indicators[0], self._SUBDIR, columns=columns, where=where)

        # Multiplos indicadores: concatena com identificador
        dfs = []
        for ind in indicators:
            df = self._qe.read(ind, self._SUBDIR, columns=columns, where=where)
            if not df.empty:
                df['indicator'] = ind
                dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        return pd.concat(dfs, ignore_index=True)

    def available(self, endpoint: str = None) -> list[str]:
        """
        Lista indicadores disponiveis.

        Args:
            endpoint: Filtrar por tipo de endpoint

        Returns:
            Lista de nomes de indicadores

        Examples:
            >>> expectations.available()
            ['ipca_anual', 'igpm_anual', 'pib_anual', ...]
        """
        if endpoint:
            return [k for k, v in EXPECTATIONS_CONFIG.items() if v.get('endpoint') == endpoint]
        return list(EXPECTATIONS_CONFIG.keys())

    def info(self, indicator: str = None) -> dict:
        """
        Retorna informacoes sobre indicador(es).

        Args:
            indicator: Nome do indicador. None = todos.

        Returns:
            Dict com informacoes do(s) indicador(es)

        Examples:
            >>> expectations.info('ipca_anual')
            {'endpoint': 'top5_anuais', 'indicator': 'IPCA', ...}
        """
        if indicator:
            if indicator not in EXPECTATIONS_CONFIG:
                raise KeyError(f"Indicador '{indicator}' nao encontrado")
            return EXPECTATIONS_CONFIG[indicator].copy()
        return EXPECTATIONS_CONFIG.copy()
