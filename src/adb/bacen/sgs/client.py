from bcb import sgs
import pandas as pd
from datetime import datetime, timedelta


class SGSClient:
    """
    Cliente para o Sistema Gerenciador de Series Temporais (SGS) do BCB.
    """

    def __init__(self):
        """Inicializa o cliente SGS."""
        pass

    def query(
        self,
        codes: dict[str, int],
        start_date: str = None,
        end_date: str = None,
        last: int = None
    ) -> pd.DataFrame:
        """
        Busca series temporais do SGS.

        Alias semantico para get_series() - consistencia com ExpectationsClient.

        Args:
            codes: Dicionario {nome: codigo_sgs}
            start_date: Data inicial 'YYYY-MM-DD' (opcional)
            end_date: Data final 'YYYY-MM-DD' (opcional)
            last: Numero de ultimos registros (opcional)

        Returns:
            DataFrame com as series solicitadas
        """
        return self.get_series(codes, start_date, end_date, last)

    def get_series(
        self,
        codes: dict[str, int],
        start_date: str = None,
        end_date: str = None,
        last: int = None
    ) -> pd.DataFrame:
        """
        Busca series temporais do SGS.

        Args:
            codes: Dicionario {nome: codigo_sgs}
            start_date: Data inicial 'YYYY-MM-DD' (opcional)
            end_date: Data final 'YYYY-MM-DD' (opcional)
            last: Numero de ultimos registros (opcional)

        Returns:
            DataFrame com as series solicitadas
        """
        try:
            df = sgs.get(codes, start=start_date, end=end_date, last=last)
            return df
        except Exception as e:
            print(f"Erro ao buscar dados SGS: {e}")
            return pd.DataFrame()

    def get_single_series(
        self,
        name: str,
        code: int,
        start_date: str = None,
        end_date: str = None,
        last: int = None
    ) -> pd.DataFrame:
        """
        Busca uma unica serie temporal do SGS.

        Args:
            name: Nome para a coluna
            code: Codigo SGS
            start_date: Data inicial 'YYYY-MM-DD' (opcional)
            end_date: Data final 'YYYY-MM-DD' (opcional)
            last: Numero de ultimos registros (opcional)

        Returns:
            DataFrame com a serie solicitada
        """
        return self.get_series({name: code}, start_date, end_date, last)

    # get_historical e get_incremental removidos (logica movida para Collector)

    # =========================================================================
    # API UNIFICADA (Recomendada)
    # =========================================================================

    def get_data(
        self,
        code: int,
        name: str,
        frequency: str,
        start_date: str = None,
        verbose: bool = False,
    ) -> pd.DataFrame:
        """
        Busca serie temporal do SGS.

        Metodo unificado que substitui get_historical() e get_incremental().
        Usado pelo SGSCollector via fetch_and_sync() do DataManager.

        Args:
            code: Codigo SGS do indicador
            name: Nome para a coluna no DataFrame
            frequency: 'daily' ou 'monthly'
            start_date: Data inicial 'YYYY-MM-DD' (None = historico completo desde 1980)
            verbose: Deprecado, mantido para compatibilidade

        Returns:
            DataFrame com serie temporal
        """
        # Se nao tem start_date, busca historico completo
        if start_date is None:
            start_date = '1980-01-01'

        if frequency == 'daily':
            # Series diarias: usar chunking (API limita ~10 anos por request)
            df = self._fetch_with_chunking(code, name, start_date)
        else:
            # Series mensais: busca direta
            df = self._fetch_series(code, name, start_date, None)

        if df.empty:
            return df

        # Renomear coluna para 'value' (padrao do DataManager)
        if name in df.columns:
            df = df.rename(columns={name: 'value'})

        return df

    def _fetch_with_chunking(
        self,
        code: int,
        name: str,
        start_date: str,
    ) -> pd.DataFrame:
        """
        Busca serie diaria com chunking de 10 anos.

        A API do BCB limita series diarias a ~10 anos por consulta.
        """
        start_year = int(start_date[:4])
        current_year = datetime.now().year

        chunks = []
        for chunk_start in range(start_year, current_year + 1, 10):
            chunk_end = min(chunk_start + 9, current_year)

            # Ajustar data inicial do primeiro chunk
            if chunk_start == start_year:
                chunk_start_date = start_date
            else:
                chunk_start_date = f'{chunk_start}-01-01'

            end_date = f'{chunk_end}-12-31'

            chunk = self._fetch_series(code, name, chunk_start_date, end_date)

            if not chunk.empty:
                chunks.append(chunk)

        if not chunks:
            return pd.DataFrame()

        df = pd.concat(chunks)
        df = df[~df.index.duplicated(keep='last')]
        df = df.sort_index()

        return df

    # =========================================================================
    # METODOS INTERNOS
    # =========================================================================

    def _fetch_series(
        self,
        code: int,
        name: str,
        start_date: str,
        end_date: str = None
    ) -> pd.DataFrame:
        """Metodo interno para buscar serie com tratamento de erro."""
        try:
            df = sgs.get({name: code}, start=start_date, end=end_date)
            return df
        except Exception:
            # Silenciosamente retorna vazio para periodos sem dados
            return pd.DataFrame()
