"""
Cliente FTP para download de microdados do Novo CAGED.

Baixa arquivos 7z diretamente em memoria (sem salvar no disco)
e extrai CSVs para DataFrames.
"""

from ftplib import FTP
from io import BytesIO
import tempfile
from pathlib import Path

import py7zr
import pandas as pd


# Colunas que podem ter formato inconsistente (com/sem virgula decimal)
# dependendo do mes. Precisam ser convertidas para float explicitamente.
NUMERIC_COLUMNS = [
    'horascontratuais',
    'salário',
    'valorsaláriofixo',
]


def _convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Converte colunas para numerico de forma robusta."""
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


class CAGEDClient:
    """Cliente FTP para download de microdados do Novo CAGED."""

    FTP_HOST = "ftp.mtps.gov.br"
    BASE_PATH = "/pdet/microdados/NOVO CAGED"

    def __init__(self, timeout: int = 300):
        """
        Inicializa o cliente.

        Args:
            timeout: Timeout em segundos para conexao FTP (default: 300)
        """
        self.timeout = timeout
        self._ftp: FTP | None = None

    def connect(self) -> FTP:
        """
        Conecta ao servidor FTP (anonymous).

        Returns:
            Instancia FTP conectada
        """
        self._ftp = FTP(self.FTP_HOST, timeout=self.timeout)
        self._ftp.encoding = 'latin-1'  # Servidor usa Latin-1
        self._ftp.login()  # anonymous
        return self._ftp

    def disconnect(self):
        """Fecha conexao FTP."""
        if self._ftp:
            try:
                self._ftp.quit()
            except Exception:
                pass
            self._ftp = None

    def _ensure_connected(self):
        """Reconecta se necessario (servidor fecha conexoes ociosas)."""
        if self._ftp is None:
            self.connect()
            return

        try:
            self._ftp.voidcmd("NOOP")
        except Exception:
            self.connect()

    def _build_filepath(self, prefix: str, year: int, month: int) -> str:
        """
        Monta caminho do arquivo no FTP.

        Args:
            prefix: CAGEDMOV, CAGEDFOR ou CAGEDEXC
            year: Ano
            month: Mes

        Returns:
            Caminho completo no FTP
        """
        ym = f"{year}{month:02d}"
        return f"{self.BASE_PATH}/{year}/{ym}/{prefix}{ym}.7z"

    def download_to_memory(self, filepath: str) -> BytesIO:
        """
        Baixa arquivo para memoria (BytesIO).

        Args:
            filepath: Caminho do arquivo no FTP

        Returns:
            BytesIO com conteudo do arquivo
        """
        self._ensure_connected()
        buffer = BytesIO()
        self._ftp.retrbinary(f"RETR {filepath}", buffer.write)
        buffer.seek(0)
        return buffer

    def read_7z_from_buffer(
        self,
        buffer: BytesIO,
        encoding: str = "utf-8",
        **read_csv_kwargs,
    ) -> pd.DataFrame:
        """
        Extrai CSV do buffer 7z e retorna DataFrame.

        Args:
            buffer: BytesIO com arquivo 7z
            encoding: Encoding do CSV (default: utf-8)
            **read_csv_kwargs: Args adicionais para pd.read_csv

        Returns:
            DataFrame com dados do CSV
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Extrai para diretorio temporario
            with py7zr.SevenZipFile(buffer, mode='r') as archive:
                archive.extractall(path=tmpdir)

            # Encontra o arquivo CSV extraido
            tmppath = Path(tmpdir)
            csv_files = list(tmppath.glob("*.txt")) + list(tmppath.glob("*.csv"))

            if not csv_files:
                raise ValueError("Nenhum arquivo CSV/TXT encontrado no 7z")

            csv_path = csv_files[0]

            # Le o CSV
            df = pd.read_csv(
                csv_path,
                encoding=encoding,
                sep=";",
                decimal=",",  # Padrao brasileiro
                low_memory=False,
                **read_csv_kwargs,
            )

        return df

    def get_data(
        self,
        prefix: str,
        year: int,
        month: int,
        verbose: bool = False,
    ) -> pd.DataFrame:
        """
        Baixa e retorna dados de um periodo.

        Args:
            prefix: CAGEDMOV, CAGEDFOR ou CAGEDEXC
            year: Ano (2020+)
            month: Mes (1-12)
            verbose: Imprimir progresso

        Returns:
            DataFrame com dados do periodo (vazio se erro)
        """
        filepath = self._build_filepath(prefix, year, month)

        if verbose:
            print(f"  Baixando {prefix} {year}-{month:02d}...")

        try:
            buffer = self.download_to_memory(filepath)
            # Dados CAGED usam UTF-8
            df = self.read_7z_from_buffer(buffer, encoding='utf-8')

            # Garante tipos numericos consistentes
            df = _convert_numeric_columns(df)

            # Adiciona colunas de referencia
            df['ano_ref'] = year
            df['mes_ref'] = month

            if verbose:
                print(f"    {len(df):,} registros")

            return df

        except Exception as e:
            if verbose:
                print(f"    Erro: {e}")
            return pd.DataFrame()

    def list_files(self, year: int = None) -> list[str]:
        """
        Lista arquivos disponiveis no FTP.

        Args:
            year: Ano para filtrar (None = todos)

        Returns:
            Lista de caminhos de arquivos
        """
        self._ensure_connected()

        if year:
            path = f"{self.BASE_PATH}/{year}"
        else:
            path = self.BASE_PATH

        try:
            return self._ftp.nlst(path)
        except Exception:
            return []
