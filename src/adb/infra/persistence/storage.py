"""
Gerenciador de persistencia de dados em formato Parquet.

Responsavel por operacoes de CRUD em arquivos Parquet.
Usado por todos os collectors do projeto.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Protocol

import duckdb
import pandas as pd

from adb.shared.utils.dates import normalize_index


# =========================================================================
# Callback Protocol para desacoplar storage de display
# =========================================================================


class StorageCallback(Protocol):
    """Protocolo para feedback de operacoes de storage."""

    def on_saved(self, path: str) -> None:
        """Chamado quando arquivo e salvo."""
        ...

    def on_appended(self, path: str) -> None:
        """Chamado quando dados sao adicionados a arquivo existente."""
        ...


class NullCallback:
    """Implementacao silenciosa (default)."""

    def on_saved(self, path: str) -> None:
        """Nao faz nada."""
        pass

    def on_appended(self, path: str) -> None:
        """Nao faz nada."""
        pass


class DisplayCallback:
    """Adapter que conecta storage ao display."""

    def __init__(self):
        from adb.ui.display import get_display

        self._display = get_display()

    def on_saved(self, path: str) -> None:
        """Exibe mensagem de arquivo salvo."""
        self._display.saved(path)

    def on_appended(self, path: str) -> None:
        """Exibe mensagem de dados adicionados."""
        self._display.appended(path)


class DataManager:
    """
    Gerenciador de persistencia em Parquet para indicadores economicos.

    Responsabilidades:
    - Salvar/ler/append de arquivos Parquet
    - Consolidacao de multiplos arquivos
    - Controle de coleta incremental (fetch_and_sync)

    Para queries SQL, use QueryEngine de adb.infra.persistence.query.
    """

    def __init__(
        self,
        base_path: Path | None = None,
        callback: StorageCallback | None = None,
    ):
        """
        Inicializa o gerenciador de dados.

        Args:
            base_path: Caminho base para diretorio data/ (opcional, usa DATA_PATH se None)
            callback: Callback para feedback de operacoes (opcional, default silencioso)
        """
        from adb.infra.config import DATA_PATH

        self.base_path = Path(base_path) if base_path else DATA_PATH
        self.raw_path = self.base_path / "raw"
        self.processed_path = self.base_path / "processed"

        # Composicao: usa QueryEngine para leituras otimizadas (DuckDB)
        from adb.infra.persistence.query import QueryEngine

        self._qe = QueryEngine(self.base_path)

        # Callback para feedback de operacoes (default silencioso)
        self._callback = callback or NullCallback()

    # =========================================================================
    # CRUD Principal
    # =========================================================================

    def save(
        self,
        df: pd.DataFrame,
        filename: str,
        subdir: str = "daily",
        format: str = "parquet",
        metadata: dict | None = None,
        verbose: bool = False,
    ):
        """
        Salva DataFrame em arquivo.

        Args:
            df: DataFrame para salvar
            filename: Nome do arquivo (sem extensao)
            subdir: Subdiretorio dentro de raw/ (ex: 'daily', 'monthly', 'expectations')
            format: Formato do arquivo ('parquet' ou 'csv')
            metadata: Dicionario com metadata adicional (opcional)
            verbose: Se True, imprime caminho salvo
        """
        output_dir = self.raw_path / subdir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Padronizar índice de data antes de salvar (usa método do QueryEngine)
        df = normalize_index(df)

        # Adicionar metadata ao DataFrame
        df.attrs["filename"] = filename
        df.attrs["subdir"] = subdir
        df.attrs["saved_at"] = datetime.now().isoformat()
        if metadata:
            df.attrs.update(metadata)

        if format == "parquet":
            filepath = output_dir / f"{filename}.parquet"
            df.to_parquet(filepath, engine="pyarrow", compression="snappy", index=True)
        elif format == "csv":
            filepath = output_dir / f"{filename}.csv"
            df.to_csv(filepath, index=True)
        else:
            raise ValueError(
                f"Formato '{format}' nao suportado. Use 'parquet' ou 'csv'."
            )

        if verbose:
            self._callback.on_saved(str(filepath.relative_to(self.base_path)))

    def read(
        self,
        filename: str,
        subdir: str = "daily",
    ) -> pd.DataFrame:
        """
        Le arquivo de dados via DuckDB (otimizado).

        Args:
            filename: Nome do arquivo (sem extensao)
            subdir: Subdiretorio dentro de raw/

        Returns:
            DataFrame com dados (vazio se arquivo nao existe)
        """
        filepath = self.raw_path / subdir / f"{filename}.parquet"

        if not filepath.exists():
            # Tentar CSV como fallback
            csv_path = self.raw_path / subdir / f"{filename}.csv"
            if csv_path.exists():
                return pd.read_csv(csv_path, index_col=0, parse_dates=True)
            return pd.DataFrame()

        # Usa QueryEngine (DuckDB) para leitura otimizada
        return self._qe.read(filename, subdir)

    def get_metadata(
        self,
        filename: str,
        subdir: str = "daily",
    ) -> dict | None:
        """
        Retorna metadados do arquivo (count, datas) de forma otimizada.

        Args:
            filename: Nome do arquivo (sem extensao)
            subdir: Subdiretorio dentro de raw/

        Returns:
            Dict com metadados ou None se arquivo nao existe
        """
        return self._qe.get_metadata(filename, subdir)

    def append(
        self,
        df: pd.DataFrame,
        filename: str,
        subdir: str = "daily",
        dedup: bool = True,
        verbose: bool = False,
    ):
        """
        Adiciona novos dados a um arquivo existente (update incremental).

        Usa DuckDB para streaming: le Parquet existente + novos dados sem
        carregar tudo na RAM, escreve para arquivo temporario e faz replace atomico.

        Args:
            df: DataFrame com novos dados
            filename: Nome do arquivo
            subdir: Subdiretorio dentro de raw/
            dedup: Se True, remove duplicatas por coluna date (para series temporais).
                   Se False, mantem todos os registros (para microdados como CAGED).
            verbose: Se True, imprime progresso
        """
        filepath = self.raw_path / subdir / f"{filename}.parquet"

        # Primeira insercao: simplesmente salvar
        if not filepath.exists():
            if not dedup:
                df = df.reset_index(drop=True)
            self.save(df, filename, subdir, verbose=verbose)
            return

        # Normalizar novo DataFrame antes de append
        df = normalize_index(df)

        # Arquivo temporario para escrita atomica
        # mkstemp retorna fd aberto; fechar imediatamente para DuckDB poder usar o path
        temp_fd, temp_path_str = tempfile.mkstemp(
            suffix=".parquet", dir=filepath.parent
        )
        os.close(temp_fd)
        temp_path = Path(temp_path_str)

        try:
            # Registrar DataFrame como view temporaria no DuckDB
            duckdb.register("_new_data", df.reset_index())

            if dedup:
                # Streaming com deduplicacao por coluna 'date'
                # ROW_NUMBER particiona por date, mantendo o registro mais recente (do novo df)
                # UNION ALL BY NAME casa colunas por nome (nao posicao), evitando erro de tipo
                # quando ordem das colunas difere entre Parquet (PyArrow) e DataFrame (reset_index)
                query = f"""
                    COPY (
                        SELECT * EXCLUDE (_rn) FROM (
                            SELECT *, ROW_NUMBER() OVER (PARTITION BY date ORDER BY _source DESC) as _rn
                            FROM (
                                SELECT *, 0 as _source FROM '{filepath}'
                                UNION ALL BY NAME
                                SELECT *, 1 as _source FROM _new_data
                            )
                        ) WHERE _rn = 1
                        ORDER BY date
                    ) TO '{temp_path}' (FORMAT 'parquet', COMPRESSION 'snappy')
                """
            else:
                # Streaming sem deduplicacao (append puro)
                # UNION ALL BY NAME evita erro de conversao de tipos por ordem de colunas
                query = f"""
                    COPY (
                        SELECT * FROM '{filepath}'
                        UNION ALL BY NAME
                        SELECT * FROM _new_data
                    ) TO '{temp_path}' (FORMAT 'parquet', COMPRESSION 'snappy')
                """

            try:
                duckdb.sql(query)
            finally:
                duckdb.unregister("_new_data")

            # Replace atomico
            temp_path.replace(filepath)

            if verbose:
                self._callback.on_appended(str(filepath.relative_to(self.base_path)))

        except Exception as e:
            # Cleanup em caso de erro
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise e

    # =========================================================================
    # Listagem e Metadados
    # =========================================================================

    def list_files(
        self,
        subdir: str = "daily",
    ) -> list[str]:
        """
        Lista arquivos salvos em um subdiretorio.

        Args:
            subdir: Subdiretorio dentro de raw/

        Returns:
            Lista de nomes de arquivos (sem extensao)
        """
        dir_path = self.raw_path / subdir

        if not dir_path.exists():
            return []

        return [f.stem for f in dir_path.glob("*.parquet")]

    def get_last_date(
        self,
        filename: str,
        subdir: str = "daily",
    ):
        """
        Retorna a ultima data disponivel em um arquivo.

        Otimizado: usa DuckDB para buscar apenas MAX(date) sem carregar
        o arquivo inteiro na memoria.

        Args:
            filename: Nome do arquivo
            subdir: Subdiretorio dentro de raw/

        Returns:
            datetime da ultima data ou None se nao existir
        """
        filepath = self.raw_path / subdir / f"{filename}.parquet"

        if not filepath.exists():
            return None

        # Tenta coluna 'date' (padronizado via normalize_index no save)
        try:
            result = self._qe.sql(f"SELECT MAX(date) as max_date FROM '{filepath}'")
            if not result.empty and result["max_date"].iloc[0] is not None:
                return pd.to_datetime(result["max_date"].iloc[0])
        except Exception:
            pass

        return None

    def is_first_run(self, subdir: str) -> bool:
        """
        Verifica se e primeira execucao (subdiretorio nao existe ou esta vazio).

        Args:
            subdir: Subdiretorio dentro de raw/

        Returns:
            True se nao existem arquivos no subdiretorio
        """
        path = self.raw_path / subdir
        if not path.exists():
            return True
        return len(list(path.glob("*.parquet"))) == 0

    def get_file_path(self, filename: str, subdir: str) -> Path:
        """
        Retorna o caminho completo do arquivo.

        Args:
            filename: Nome do arquivo (sem extensao)
            subdir: Subdiretorio

        Returns:
            Path do arquivo Parquet
        """
        return self.raw_path / subdir / f"{filename}.parquet"
