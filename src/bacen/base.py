"""
Classe base para coletores do BCB.

Fornece metodos utilitarios comuns para SGS e Expectations.
"""

from pathlib import Path
import pandas as pd

from data import DataManager


class BaseCollector:
    """
    Classe base para coletores do BCB.

    Fornece:
    - Delegacoes para DataManager (save, read, list_files)
    - get_status() padronizado baseado em arquivos
    - Atributos de configuracao (default_subdir, default_consolidate_subdirs)

    Subclasses devem definir:
    - default_subdir: str - subdiretorio padrao para operacoes
    - default_consolidate_subdirs: list[str] - subdiretorios para consolidacao
    """

    default_subdir: str = 'raw'
    default_consolidate_subdirs: list[str] = ['raw']

    def __init__(self, data_path: Path):
        """
        Inicializa o coletor base.

        Args:
            data_path: Caminho para diretorio data/
        """
        self.data_path = Path(data_path)
        self.data_manager = DataManager(data_path)

    # =========================================================================
    # Logging (output padronizado)
    # =========================================================================

    def _log_fetch_start(self, name: str, start_date: str = None, verbose: bool = True):
        """Loga inicio de fetch de indicador."""
        if not verbose:
            return
        if start_date:
            print(f"  Buscando {name} desde {start_date}...")
        else:
            print(f"  Buscando {name} (historico completo)...")

    def _log_fetch_result(self, name: str, count: int, verbose: bool = True):
        """Loga resultado de fetch de indicador."""
        if not verbose:
            return
        if count:
            print(f"  {count:,} registros")
        else:
            print(f"  Sem dados disponiveis")

    # =========================================================================
    # Delegacoes para DataManager
    # =========================================================================

    def save(
        self,
        df: pd.DataFrame,
        filename: str,
        subdir: str = None,
        **kwargs
    ):
        """
        Salva DataFrame em arquivo.

        Args:
            df: DataFrame para salvar
            filename: Nome do arquivo (sem extensao)
            subdir: Subdiretorio (default: default_subdir)
            **kwargs: Argumentos adicionais para DataManager.save()
        """
        return self.data_manager.save(
            df, filename, subdir or self.default_subdir, **kwargs
        )

    def read(
        self,
        filename: str,
        subdir: str = None,
    ) -> pd.DataFrame:
        """
        Le arquivo de dados.

        Args:
            filename: Nome do arquivo (sem extensao)
            subdir: Subdiretorio (default: default_subdir)

        Returns:
            DataFrame com dados (vazio se arquivo nao existe)
        """
        return self.data_manager.read(filename, subdir or self.default_subdir)

    def list_files(self, subdir: str = None) -> list[str]:
        """
        Lista arquivos salvos em um subdiretorio.

        Args:
            subdir: Subdiretorio (default: default_subdir)

        Returns:
            Lista de nomes de arquivos (sem extensao)
        """
        return self.data_manager.list_files(subdir or self.default_subdir)

    # =========================================================================
    # Status
    # =========================================================================

    def get_status(self, subdir: str = None) -> pd.DataFrame:
        """
        Retorna status dos arquivos salvos.

        Args:
            subdir: Subdiretorio (default: default_subdir)

        Returns:
            DataFrame com status de cada arquivo
        """
        subdir = subdir or self.default_subdir
        files = self.data_manager.list_files(subdir)

        if not files:
            return pd.DataFrame()

        status_data = []
        for filename in files:
            df = self.data_manager.read(filename, subdir)

            if df.empty:
                status_data.append({
                    'arquivo': filename,
                    'subdir': subdir,
                    'registros': 0,
                    'colunas': 0,
                    'primeira_data': None,
                    'ultima_data': None,
                    'status': 'Vazio',
                })
            else:
                # Tentar identificar range de datas
                primeira_data = None
                ultima_data = None

                # Verificar se indice e datetime
                if pd.api.types.is_datetime64_any_dtype(df.index):
                    primeira_data = df.index.min()
                    ultima_data = df.index.max()
                # Verificar coluna Data
                elif 'Data' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Data']):
                    primeira_data = df['Data'].min()
                    ultima_data = df['Data'].max()

                status_data.append({
                    'arquivo': filename,
                    'subdir': subdir,
                    'registros': len(df),
                    'colunas': len(df.columns),
                    'primeira_data': primeira_data,
                    'ultima_data': ultima_data,
                    'status': 'OK',
                })

        return pd.DataFrame(status_data)
