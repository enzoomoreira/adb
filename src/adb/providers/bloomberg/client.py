"""
Cliente Bloomberg via xbbg.

Wrapper que adapta xbbg.blp ao padrao do projeto.
"""

import contextlib
import io
import sys
from datetime import datetime, timedelta

import pandas as pd
import xbbg.blp as blp

from adb.infra.log import get_logger
from adb.infra.resilience import retry
from .indicators import LOOKBACK_DAYS


@contextlib.contextmanager
def _capture_external_output(logger):
    """
    Captura stdout/stderr de bibliotecas externas e envia para logger.

    O SDK xbbg (Bloomberg) imprime mensagens de debug diretamente no stdout/stderr,
    gerando ruido no terminal. Este context manager captura esse output e redireciona
    para o arquivo de log, mantendo o terminal limpo.

    Args:
        logger: Logger para onde redirecionar o output capturado

    Yields:
        None
    """
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr

    try:
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        yield
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr

        # Enviar output capturado para o log
        stdout_content = stdout_capture.getvalue().strip()
        stderr_content = stderr_capture.getvalue().strip()

        if stdout_content:
            for line in stdout_content.split('\n'):
                if line.strip():
                    logger.debug(f"SDK stdout: {line}")

        if stderr_content:
            for line in stderr_content.split('\n'):
                if line.strip():
                    logger.warning(f"SDK stderr: {line}")


class BloombergClient:
    """
    Cliente Bloomberg via xbbg.

    Wrapper que adapta xbbg.blp ao padrao do projeto:
    - Indice: DatetimeIndex
    - Coluna: 'value'
    - Lookback limitado para evitar quotas
    """

    def __init__(self):
        """Inicializa cliente Bloomberg."""
        self.logger = get_logger(self.__class__.__name__)

    # =========================================================================
    # Metodos Publicos
    # =========================================================================

    @retry(max_attempts=2, delay=1.0, exceptions=(RuntimeError, TimeoutError, OSError))
    def get_data(
        self,
        ticker: str,
        field: str,
        name: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """
        Busca serie temporal historica do Bloomberg.

        Metodo principal usado por BloombergCollector via fetch_and_sync().

        Args:
            ticker: Bloomberg ticker (ex: 'MXWD Index', 'IBOV Index')
            field: Bloomberg field (ex: 'PX_LAST', 'BEST_PE_RATIO')
            name: Nome para logging (opcional)
            start_date: Data inicial 'YYYY-MM-DD' (None = usa LOOKBACK_DAYS)
            end_date: Data final 'YYYY-MM-DD' (None = hoje)

        Returns:
            DataFrame com DatetimeIndex e coluna 'value'
            Retorna DataFrame vazio em caso de erro
        """
        try:
            # Defesa minima: trata NaT como None
            if pd.isna(start_date):
                start_date = None
            if pd.isna(end_date):
                end_date = None

            # Se start_date=None, limitar a LOOKBACK_DAYS para evitar quotas
            if start_date is None:
                start_date = (datetime.today() - timedelta(days=LOOKBACK_DAYS)).strftime(
                    "%Y-%m-%d"
                )

            # Se end_date=None, usa hoje
            if end_date is None:
                end_date = datetime.today().strftime("%Y-%m-%d")

            # xbbg.blp.bdh retorna DataFrame com:
            # - Index: DatetimeIndex
            # - Columns: MultiIndex (ticker, field) se multiplos tickers/fields
            #            ou Index simples se 1 ticker + 1 field
            # Captura stdout/stderr do SDK para evitar ruido no terminal
            with _capture_external_output(self.logger):
                df = blp.bdh(
                    tickers=ticker,
                    flds=field,
                    start_date=start_date,
                    end_date=end_date,
                )

            if df is None or df.empty:
                return pd.DataFrame()

            # Normalizar para DatetimeIndex + coluna 'value'
            df = self._normalize_dataframe(df, ticker, field)

            return df

        except Exception as e:
            self.logger.error(f"Erro ao buscar {ticker}/{field}: {e}")
            return pd.DataFrame()

    def get_reference_data(
        self,
        tickers: list[str] | str,
        fields: list[str] | str,
    ) -> pd.DataFrame:
        """
        Busca reference data (ponto unico, nao serie temporal).

        Util para metadados (NAME, SECURITY_TYP, etc).

        Args:
            tickers: Ticker(s) Bloomberg
            fields: Field(s) Bloomberg

        Returns:
            DataFrame com tickers no index e fields nas colunas
            Retorna DataFrame vazio em caso de erro
        """
        try:
            with _capture_external_output(self.logger):
                df = blp.bdp(tickers, fields)
            return df if df is not None else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    # =========================================================================
    # Metodos Internos (Helpers)
    # =========================================================================

    def _normalize_dataframe(
        self,
        df: pd.DataFrame,
        ticker: str,
        field: str,
    ) -> pd.DataFrame:
        """
        Normaliza DataFrame do xbbg para padrao do projeto.

        Transformacoes:
        1. Remove timezone se presente
        2. Extrai coluna especifica de MultiIndex
        3. Renomeia para 'value'
        4. Remove NaN
        5. Ordena por data
        6. Define nome do indice como 'date'

        Args:
            df: DataFrame retornado por xbbg.blp.bdh
            ticker: Ticker solicitado
            field: Field solicitado

        Returns:
            DataFrame normalizado com DatetimeIndex + coluna 'value'
        """
        if df.empty:
            return df

        # 1. Garantir DatetimeIndex sem timezone
        if isinstance(df.index, pd.DatetimeIndex):
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)

        # 2. Extrair coluna do MultiIndex ou Index simples
        # xbbg.bdh retorna MultiIndex (ticker, field) quando multiplos
        if isinstance(df.columns, pd.MultiIndex):
            # Pegar coluna (ticker, field)
            if (ticker, field) in df.columns:
                df = df[[(ticker, field)]].copy()
                df.columns = ["value"]
            else:
                # Tentar primeira coluna que contenha o field
                matching = [c for c in df.columns if c[1] == field]
                if matching:
                    df = df[[matching[0]]].copy()
                    df.columns = ["value"]
                else:
                    return pd.DataFrame()
        else:
            # Index simples: renomear unica coluna para 'value'
            if field in df.columns:
                df = df[[field]].rename(columns={field: "value"})
            elif len(df.columns) == 1:
                df = df.rename(columns={df.columns[0]: "value"})

        # 3. Remover NaN
        df = df.dropna(subset=["value"])

        # 4. Ordenar por data
        df = df.sort_index()

        # 5. Garantir nome do indice para Parquet
        df.index.name = 'date'

        return df
