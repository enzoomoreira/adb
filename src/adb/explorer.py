"""
Classe base para explorers de dados.

Fornece implementacao comum para leitura, listagem e coleta de dados,
reduzindo duplicacao entre os explorers especificos.
"""

import pandas as pd

from adb.infra.log import get_logger
from adb.utils import normalize_index, parse_date


class BaseExplorer:
    """Classe base para explorers de dados.

    Subclasses devem definir:
    - _CONFIG: dict - Configuracao de indicadores
    - _SUBDIR_TEMPLATE: str - Template de subdir (ex: "bacen/sgs/{frequency}")
    - _CLIENT_CLASS: type - Classe do client
    - _TITLE: str - Titulo para banner de coleta

    Subclasses podem sobrescrever:
    - _DATE_COLUMN: str - Nome da coluna de data (default: 'date')
    - _fetch_one(): Para logica de fetch customizada
    - _join(): Para logica de join diferente
    """

    _CONFIG: dict
    _SUBDIR_TEMPLATE: str
    _CLIENT_CLASS: type
    _TITLE: str
    _DATE_COLUMN: str = "date"

    def __init__(self, query_engine=None):
        from adb.infra.query import QueryEngine

        self._qe = query_engine or QueryEngine()
        self.logger = get_logger(self.__class__.__name__)

    # =========================================================================
    # Metodos Internos (Extension Points)
    # =========================================================================

    def _subdir(self, indicator: str) -> str:
        """Retorna subdiretorio para um indicador via template."""
        template = self._SUBDIR_TEMPLATE
        if "{frequency}" in template:
            frequency = self._CONFIG[indicator].get("frequency", "daily")
            return template.format(frequency=frequency)
        return template

    def _where(self, start: str | None = None, end: str | None = None) -> str | None:
        """Constroi clausula WHERE para filtro de data."""
        where_clauses = []
        if start:
            where_clauses.append(f"{self._DATE_COLUMN} >= '{parse_date(start)}'")
        if end:
            where_clauses.append(f"{self._DATE_COLUMN} <= '{parse_date(end)}'")
        return " AND ".join(where_clauses) if where_clauses else None

    def _fetch_one(
        self, indicator: str, start: str | None, end: str | None
    ) -> pd.DataFrame:
        """Busca um indicador diretamente da API (sem disco)."""
        config = self._CONFIG[indicator]
        client = self._CLIENT_CLASS()
        return client.get_data(config, start, end)

    def _join(self, dfs: list, indicators: tuple) -> pd.DataFrame:
        """
        Junta multiplos DataFrames por data.

        Override para logica diferente (ex: Expectations usa concat).
        """
        if not dfs:
            return pd.DataFrame()

        # pd.concat com axis=1 faz outer join no indice automaticamente
        return pd.concat(dfs, axis=1).sort_index()

    # =========================================================================
    # API Publica
    # =========================================================================

    def read(
        self,
        *indicators: str,
        start: str | None = None,
        end: str | None = None,
        columns: list[str] | None = None,
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
            - Um indicador: DatetimeIndex + coluna com nome do indicador
            - Multiplos: DatetimeIndex + coluna por indicador (join por data)
        """
        # Default: todos os indicadores
        if not indicators:
            indicators = tuple(self._CONFIG.keys())

        # Validar indicadores
        for ind in indicators:
            if ind not in self._CONFIG:
                available = ", ".join(self._CONFIG.keys())
                raise KeyError(
                    f"Indicador '{ind}' nao encontrado. Disponiveis: {available}"
                )

        self.logger.debug(f"Lendo {len(indicators)} indicador(es): {indicators}")

        where = self._where(start, end)

        # Um indicador: retorna direto
        if len(indicators) == 1:
            subdir = self._subdir(indicators[0])
            df = self._qe.read(indicators[0], subdir, columns=columns, where=where)
            df = normalize_index(df)
            if df.empty:
                self.logger.warning(f"Nenhum dado encontrado para '{indicators[0]}'")
            if "value" in df.columns:
                df = df.rename(columns={"value": indicators[0]})
            return df

        # Multiplos indicadores: join por data
        dfs = []
        for ind in indicators:
            subdir = self._subdir(ind)
            df = self._qe.read(ind, subdir, columns=["value"], where=where)
            df = normalize_index(df)
            if not df.empty:
                df = df.rename(columns={"value": ind})
                dfs.append(df)
            else:
                self.logger.warning(f"Nenhum dado encontrado para '{ind}'")

        return self._join(dfs, indicators)

    def fetch(
        self,
        *indicators: str,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        Busca dados diretamente da API (stateless, sem disco).

        Args:
            *indicators: Nomes dos indicadores (default: todos)
            start: Data inicial (formatos: '2020', '2020-01', '2020-01-01')
            end: Data final (mesmos formatos)

        Returns:
            DataFrame com series temporais (mesma estrutura de read())
        """
        if not indicators:
            indicators = tuple(self._CONFIG.keys())

        for ind in indicators:
            if ind not in self._CONFIG:
                available = ", ".join(self._CONFIG.keys())
                raise KeyError(
                    f"Indicador '{ind}' nao encontrado. Disponiveis: {available}"
                )

        parsed_start = parse_date(start) if start else None
        parsed_end = parse_date(end) if end else None

        if len(indicators) == 1:
            df = self._fetch_one(indicators[0], parsed_start, parsed_end)
            df = normalize_index(df)
            if parsed_end and not df.empty:
                df = df[df.index <= pd.Timestamp(parsed_end)]
            if "value" in df.columns:
                df = df.rename(columns={"value": indicators[0]})
            return df

        dfs = []
        for ind in indicators:
            df = self._fetch_one(ind, parsed_start, parsed_end)
            df = normalize_index(df)
            if parsed_end and not df.empty:
                df = df[df.index <= pd.Timestamp(parsed_end)]
            if not df.empty:
                if "value" in df.columns:
                    df = df.rename(columns={"value": ind})
                dfs.append(df)

        return self._join(dfs, indicators)

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

    def info(self, indicator: str | None = None) -> dict:
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
        indicators: list[str] | str = "all",
        start: str | None = None,
        end: str | None = None,
        save: bool = True,
        verbose: bool = True,
    ) -> None:
        """Coleta dados da fonte e salva em cache local (Parquet)."""
        from adb.collector import BaseCollector

        collector = BaseCollector(
            config=self._CONFIG,
            title=self._TITLE,
            client_class=self._CLIENT_CLASS,
            subdir_template=self._SUBDIR_TEMPLATE,
        )
        collector.collect(
            indicators=indicators,
            start=start,
            end=end,
            save=save,
            verbose=verbose,
        )

    def status(self) -> pd.DataFrame:
        """Retorna status de todos os indicadores configurados.

        Inclui indicadores coletados (com metricas de saude) e nao coletados
        (marcados como NOT_COLLECTED).
        """
        from adb.collector import BaseCollector

        collector = BaseCollector(
            config=self._CONFIG,
            title=self._TITLE,
            client_class=self._CLIENT_CLASS,
            subdir_template=self._SUBDIR_TEMPLATE,
        )
        df = collector.status()

        tracked: set[str] = set(df["arquivo"].tolist()) if not df.empty else set()
        missing: set[str] = set(self.available()) - tracked

        if not missing:
            if not df.empty:
                return df.sort_values("arquivo", ignore_index=True)
            return df

        not_collected_rows: list[dict] = []
        for indicator in sorted(missing):
            row: dict = {
                "arquivo": indicator,
                "subdir": self._subdir(indicator),
                "status": "NOT_COLLECTED",
            }
            if not df.empty:
                for col in df.columns:
                    if col not in row:
                        row[col] = 0 if col in ("registros", "gaps") else None
            else:
                row.update(
                    {
                        "registros": 0,
                        "primeira_data": None,
                        "ultima_data": None,
                        "cobertura": None,
                        "gaps": 0,
                    }
                )
            not_collected_rows.append(row)

        not_collected_df = pd.DataFrame(not_collected_rows)

        if df.empty:
            result = not_collected_df
        else:
            result = pd.concat([df, not_collected_df], ignore_index=True)

        return result.sort_values("arquivo", ignore_index=True)
