"""
Cliente para a API do IPEADATA.

Wrapper do ipeadatapy adaptado aos padroes do projeto.
"""

import pandas as pd
import ipeadatapy

from adb.core.log import get_logger
from adb.core.resilience import retry


class IPEAClient:
    """
    Cliente para download de series temporais do IPEADATA.

    Adapta o formato de saida do ipeadatapy para o padrao do projeto:
    - Indice: DatetimeIndex (coluna DATE)
    - Coluna: 'value' (normalizado)
    """

    def __init__(self):
        """Inicializa o cliente IPEA."""
        self.logger = get_logger(self.__class__.__name__)

    # =========================================================================
    # Metodos Publicos
    # =========================================================================

    def get_data(
        self,
        code: str,
        name: str = None,
        start_date: str = None,
    ) -> pd.DataFrame:
        """
        Busca serie temporal do IPEADATA.

        Metodo principal usado pelo IPEACollector via fetch_and_sync().

        Args:
            code: Codigo da serie no IPEADATA (ex: 'CAGED12_SALDON12')
            name: Nome para identificacao (usado em logs, opcional)
            start_date: Data inicial 'YYYY-MM-DD' (None = historico completo)

        Returns:
            DataFrame com indice=DatetimeIndex, coluna='value'
        """
        # Determinar ano para filtro inicial (otimizacao)
        year = None
        if start_date:
            year = int(start_date[:4]) - 1  # yearGreaterThan e exclusivo

        df = self._fetch_timeseries(code, year)

        if df is None or df.empty:
            return pd.DataFrame()

        # Normalizar para padrao do projeto
        df = self._normalize_dataframe(df)

        # Filtrar por data exata (se necessario)
        if start_date and not df.empty:
            df = self._filter_by_start_date(df, start_date)

        return df

    @retry()  # usa defaults de NETWORK_EXCEPTIONS, attempts, delay
    def _fetch_timeseries(self, code: str, year: int = None) -> pd.DataFrame:
        """Busca dados brutos do IPEA com retry."""
        if year:
            return ipeadatapy.timeseries(code, yearGreaterThan=year)
        return ipeadatapy.timeseries(code)

    def get_metadata(self, code: str) -> dict:
        """
        Retorna metadados de uma serie.

        Args:
            code: Codigo da serie

        Returns:
            Dict com name, unit, frequency, source, last_update
        """
        try:
            meta = ipeadatapy.describe(code)

            if meta is None or meta.empty:
                return {}

            # describe() retorna DataFrame com uma linha
            row = meta.iloc[0]

            return {
                "name": row.get("NAME", ""),
                "unit": row.get("UNIT", ""),
                "frequency": row.get("FREQUENCY", ""),
                "source": row.get("SOURCE", ""),
                "last_update": row.get("LAST UPDATE", ""),
            }

        except Exception:
            return {}

    def list_series(self, keyword: str = None) -> pd.DataFrame:
        """
        Lista series disponiveis.

        Args:
            keyword: Filtrar por palavra-chave (opcional)

        Returns:
            DataFrame com CODE, NAME, FREQUENCY, SOURCE
        """
        try:
            if keyword:
                df = ipeadatapy.list_series(keyword)
            else:
                df = ipeadatapy.list_series()

            if df is None or df.empty:
                return pd.DataFrame()

            # Selecionar colunas relevantes
            cols = ["CODE", "NAME", "FREQUENCY", "SOURCE"]
            available_cols = [c for c in cols if c in df.columns]

            return df[available_cols]

        except Exception:
            return pd.DataFrame()

    # =========================================================================
    # Metodos Internos (Helpers)
    # =========================================================================

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza DataFrame do ipeadatapy para o padrao do projeto.

        Transformacoes:
        1. Converte coluna 'DATE' para DatetimeIndex
        2. Remove timezone (ipeadatapy retorna com -02:00/-03:00)
        3. Renomeia coluna VALUE para 'value'
        4. Remove colunas auxiliares (YEAR, MONTH, DAY, CODE, RAW DATE)
        """
        if df.empty:
            return df

        # 1. Converter DATE para datetime e remover timezone
        if "DATE" in df.columns:
            df["DATE"] = pd.to_datetime(df["DATE"]).dt.tz_localize(None)
            # Definir como indice
            df = df.set_index("DATE")
            df.index.name = None  # Padrao do projeto

        # 2. Encontrar coluna VALUE (pode ter unidade no nome, ex: "VALUE (Pessoa)")
        value_cols = [c for c in df.columns if c.startswith("VALUE")]
        if value_cols:
            value_col = value_cols[0]
            # Manter apenas coluna de valor, renomear para 'value'
            df = df[[value_col]].rename(columns={value_col: "value"})

        # 3. Ordenar por data
        df = df.sort_index()

        return df

    def _filter_by_start_date(
        self,
        df: pd.DataFrame,
        start_date: str
    ) -> pd.DataFrame:
        """
        Filtra DataFrame por data inicial.

        O ipeadatapy.timeseries() usa yearGreaterThan mas nao tem filtro
        por data exata, entao filtramos apos o download.

        Args:
            df: DataFrame com DatetimeIndex
            start_date: Data inicial 'YYYY-MM-DD'

        Returns:
            DataFrame filtrado
        """
        start = pd.to_datetime(start_date)
        return df[df.index >= start]
