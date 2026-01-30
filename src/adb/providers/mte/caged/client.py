"""
Cliente FTP para download de microdados do Novo CAGED.

Baixa arquivos 7z diretamente para disco.
A conversão para Parquet é feita pelo CAGEDCollector usando DuckDB.
"""

from ftplib import FTP
from pathlib import Path
import tempfile

from adb.infra.resilience import retry


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

    # =========================================================================
    # Metodos Publicos
    # =========================================================================

    @retry(delay=5.0, backoff_factor=2.0)
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

    # =========================================================================
    # Metodos Internos
    # =========================================================================

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

    @retry(delay=5.0, backoff_factor=2.0)
    def download_to_file(
        self,
        prefix: str,
        year: int,
        month: int,
        target_path: Path | str = None,
    ) -> Path:
        """
        Baixa arquivo 7z diretamente para disco.

        Args:
            prefix: CAGEDMOV, CAGEDFOR ou CAGEDEXC
            year: Ano (2020+)
            month: Mes (1-12)
            target_path: Caminho de destino (opcional, usa temp se None)

        Returns:
            Path do arquivo baixado

        Raises:
            Exception: Propaga erros de conexao/download apos retries
        """
        self._ensure_connected()
        
        filepath = self._build_filepath(prefix, year, month)
        
        # Se não especificou destino, usa arquivo temporário
        if target_path is None:
            ym = f"{year}{month:02d}"
            target_path = Path(tempfile.gettempdir()) / f"{prefix}{ym}.7z"
        else:
            target_path = Path(target_path)
        
        # Garantir que diretório existe
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download direto para arquivo
        with open(target_path, 'wb') as f:
            self._ftp.retrbinary(f"RETR {filepath}", f.write)
        
        return target_path

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
