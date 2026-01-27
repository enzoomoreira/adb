"""
Classe base para explorers de dados.

Fornece implementacao comum para leitura, listagem e coleta de dados,
reduzindo duplicacao entre os explorers especificos.
"""

from typing import List
import pandas as pd

from adb.core.log import get_logger
from adb.core.utils import parse_date
from adb.core.utils.dates import normalize_date_index


class BaseExplorer:
    """
    Classe base para explorers de dados.

    Subclasses devem definir:
    - _CONFIG: dict - Configuracao de indicadores
    - _SUBDIR: str - Subdiretorio padrao para arquivos
    - _COLLECTOR_CLASS: property - Classe do collector (lazy import)

    Subclasses podem sobrescrever:
    - _DATE_COLUMN: str - Nome da coluna de data (default: 'date')
    - _get_subdir(): Para subdir dinamico por indicador
    - _join_multiple(): Para logica de join diferente
    """

    _CONFIG: dict = None
    _SUBDIR: str = None
    _DATE_COLUMN: str = 'date'

    def __init__(self, query_engine=None):
        """
        Inicializa o explorer.

        Args:
            query_engine: QueryEngine customizado (opcional, cria novo se None)
        """
        from adb.core.data import QueryEngine
        self._qe = query_engine or QueryEngine()
        self.logger = get_logger(self.__class__.__name__)

    @property
    def _COLLECTOR_CLASS(self):
        """Retorna classe do collector. Sobrescrever na subclasse."""
        raise NotImplementedError("Subclasse deve implementar _COLLECTOR_CLASS")

    # =========================================================================
    # Metodos Internos (Extension Points)
    # =========================================================================

    def _get_subdir(self, indicator: str) -> str:
        """
        Retorna subdiretorio para um indicador.

        Override para subdirs dinamicos (ex: SGS com daily/monthly).
        """
        return self._SUBDIR

    def _build_where(self, start: str = None, end: str = None) -> str | None:
        """Constroi clausula WHERE para filtro de data."""
        where_clauses = []
        if start:
            where_clauses.append(f"{self._DATE_COLUMN} >= '{parse_date(start)}'")
        if end:
            where_clauses.append(f"{self._DATE_COLUMN} <= '{parse_date(end)}'")
        return " AND ".join(where_clauses) if where_clauses else None

    def _join_multiple(self, dfs: list, indicators: tuple) -> pd.DataFrame:
        """
        Junta multiplos DataFrames por data.

        Override para logica diferente (ex: Expectations usa concat).
        """
        if not dfs:
            return pd.DataFrame()

        result = dfs[0]
        for df in dfs[1:]:
            result = result.join(df, how='outer')

        return result.sort_index()

    # =========================================================================
    # API Publica
    # =========================================================================

    def read(
        self,
        *indicators: str,
        start: str = None,
        end: str = None,
        columns: List[str] = None,
    ) -> pd.DataFrame:
        """
        Le series temporais.

        Args:
            *indicators: Nomes dos indicadores
            start: Data inicial (formatos: '2020', '2020-01', '2020-01-01')
            end: Data final (mesmos formatos)
            columns: Colunas especificas (default: todas)

        Returns:
            DataFrame com series temporais
            - Um indicador: DatetimeIndex + colunas do arquivo
            - Multiplos: DatetimeIndex + coluna por indicador (join por data)
        """
        # Default: todos os indicadores
        if not indicators:
            indicators = tuple(self._CONFIG.keys())

        # Validar indicadores
        for ind in indicators:
            if ind not in self._CONFIG:
                available = ', '.join(self._CONFIG.keys())
                raise KeyError(f"Indicador '{ind}' nao encontrado. Disponiveis: {available}")

        self.logger.debug(f"Lendo {len(indicators)} indicador(es): {indicators}")

        where = self._build_where(start, end)

        # Um indicador: retorna direto
        if len(indicators) == 1:
            subdir = self._get_subdir(indicators[0])
            df = self._qe.read(indicators[0], subdir, columns=columns, where=where)
            df = normalize_date_index(df)
            if df.empty:
                self.logger.warning(f"Nenhum dado encontrado para '{indicators[0]}'")
            return df

        # Multiplos indicadores: join por data
        dfs = []
        for ind in indicators:
            subdir = self._get_subdir(ind)
            df = self._qe.read(ind, subdir, columns=['value'], where=where)
            df = normalize_date_index(df)
            if not df.empty:
                df = df.rename(columns={'value': ind})
                dfs.append(df)
            else:
                self.logger.warning(f"Nenhum dado encontrado para '{ind}'")

        return self._join_multiple(dfs, indicators)

    def available(self, **filters) -> list[str]:
        """
        Lista indicadores disponiveis.

        Args:
            **filters: Filtros por atributo do config (ex: frequency='daily')

        Returns:
            Lista de nomes de indicadores
        """
        if not filters:
            return list(self._CONFIG.keys())

        result = []
        for key, config in self._CONFIG.items():
            match = all(config.get(k) == v for k, v in filters.items())
            if match:
                result.append(key)
        return result

    def info(self, indicator: str = None) -> dict:
        """
        Retorna informacoes sobre indicador(es).

        Args:
            indicator: Nome do indicador. None = todos.

        Returns:
            Dict com informacoes do(s) indicador(es)
        """
        if indicator:
            if indicator not in self._CONFIG:
                raise KeyError(f"Indicador '{indicator}' nao encontrado")
            return self._CONFIG[indicator].copy()
        return self._CONFIG.copy()

    def collect(
        self,
        indicators: list[str] | str = 'all',
        save: bool = True,
        verbose: bool = True,
        **kwargs,
    ) -> None:
        """
        Coleta dados da fonte.

        Args:
            indicators: 'all', lista, ou string com indicador(es)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso
            **kwargs: Argumentos extras para o collector
        """
        # Logs removidos - BaseCollector ja faz banners detalhados
        collector = self._COLLECTOR_CLASS()
        collector.collect(indicators=indicators, save=save, verbose=verbose, **kwargs)

    def get_status(self) -> pd.DataFrame:
        """Retorna status dos arquivos salvos."""
        collector = self._COLLECTOR_CLASS()
        return collector.get_status()
