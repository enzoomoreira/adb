"""
Gerenciador de persistencia de dados em formato Parquet.

Responsavel por operacoes de CRUD em arquivos Parquet.
Usado por todos os collectors do projeto.
"""

from pathlib import Path
from datetime import datetime, timedelta
from typing import Callable

import pandas as pd


class DataManager:
    """
    Gerenciador de persistencia em Parquet para indicadores economicos.

    Responsabilidades:
    - Salvar/ler/append de arquivos Parquet
    - Consolidacao de multiplos arquivos
    - Controle de coleta incremental (fetch_and_sync)

    Para queries SQL, use QueryEngine de core.data.query.
    """

    def __init__(self, base_path: Path):
        """
        Inicializa o gerenciador de dados.

        Args:
            base_path: Caminho base para diretorio data/
        """
        self.base_path = Path(base_path)
        self.raw_path = self.base_path / 'raw'
        self.processed_path = self.base_path / 'processed'

    # =========================================================================
    # CRUD Principal
    # =========================================================================

    def save(
        self,
        df: pd.DataFrame,
        filename: str,
        subdir: str = 'daily',
        format: str = 'parquet',
        metadata: dict = None,
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

        # Adicionar metadata ao DataFrame
        df.attrs['filename'] = filename
        df.attrs['subdir'] = subdir
        df.attrs['saved_at'] = datetime.now().isoformat()
        if metadata:
            df.attrs.update(metadata)

        if format == 'parquet':
            filepath = output_dir / f"{filename}.parquet"
            df.to_parquet(
                filepath,
                engine='pyarrow',
                compression='snappy',
                index=True
            )
        elif format == 'csv':
            filepath = output_dir / f"{filename}.csv"
            df.to_csv(filepath, index=True)
        else:
            raise ValueError(f"Formato '{format}' nao suportado. Use 'parquet' ou 'csv'.")

        if verbose:
            print(f"Salvo: {filepath.relative_to(self.base_path)}")

    def read(
        self,
        filename: str,
        subdir: str = 'daily',
    ) -> pd.DataFrame:
        """
        Le arquivo de dados.

        Args:
            filename: Nome do arquivo (sem extensao)
            subdir: Subdiretorio dentro de raw/

        Returns:
            DataFrame com dados (vazio se arquivo nao existe)

        Note:
            Para leitura com filtros SQL, use QueryEngine.read_filtered()
        """
        filepath = self.raw_path / subdir / f"{filename}.parquet"

        if not filepath.exists():
            # Tentar CSV como fallback
            csv_path = self.raw_path / subdir / f"{filename}.csv"
            if csv_path.exists():
                return pd.read_csv(csv_path, index_col=0, parse_dates=True)
            return pd.DataFrame()

        return pd.read_parquet(filepath, engine='pyarrow')

    def append(
        self,
        df: pd.DataFrame,
        filename: str,
        subdir: str = 'daily',
        dedup: bool = True,
        verbose: bool = False,
    ):
        """
        Adiciona novos dados a um arquivo existente (update incremental).

        Args:
            df: DataFrame com novos dados
            filename: Nome do arquivo
            subdir: Subdiretorio dentro de raw/
            dedup: Se True, remove duplicatas por indice (para series temporais).
                   Se False, mantem todos os registros (para microdados como CAGED).
            verbose: Se True, imprime progresso

        Nota sobre dedup:
            - dedup=True (padrao): Para series temporais onde indice = data unica.
              Remove duplicatas mantendo o valor mais recente.
            - dedup=False: Para microdados onde cada linha e um registro unico
              (ex: CAGED). Usa ignore_index=True para resetar indices e nao
              remove nenhum registro.
        """
        existing_df = self.read(filename, subdir)

        if existing_df.empty:
            # Primeira insercao: se dedup=False, reseta indice para evitar problemas futuros
            if not dedup:
                df = df.reset_index(drop=True)
            self.save(df, filename, subdir, verbose=verbose)
            return

        # Concatena DataFrames
        # - dedup=True: mantem indices originais para poder identificar duplicatas
        # - dedup=False: usa ignore_index para criar indice sequencial unico
        combined = pd.concat([existing_df, df], ignore_index=not dedup)

        # Remove duplicatas apenas para series temporais (dedup=True)
        if dedup:
            combined = combined[~combined.index.duplicated(keep='last')]
            combined = combined.sort_index()

        # Preservar metadata existente
        combined.attrs = existing_df.attrs.copy()
        combined.attrs['last_update'] = datetime.now().isoformat()

        self.save(combined, filename, subdir, metadata=combined.attrs, verbose=verbose)

    # =========================================================================
    # Listagem e Metadados
    # =========================================================================

    def list_files(
        self,
        subdir: str = 'daily',
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

        return [f.stem for f in dir_path.glob('*.parquet')]

    def get_last_date(
        self,
        filename: str,
        subdir: str = 'daily',
    ):
        """
        Retorna a ultima data disponivel em um arquivo.

        Args:
            filename: Nome do arquivo
            subdir: Subdiretorio dentro de raw/

        Returns:
            datetime da ultima data ou None se nao existir
        """
        df = self.read(filename, subdir)
        if df.empty:
            return None

        # Verificar se indice e datetime
        if pd.api.types.is_datetime64_any_dtype(df.index):
            return df.index.max()

        # Verificar se existe coluna 'Data' com datetime
        if 'Data' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Data']):
            return df['Data'].max()

        # Fallback: tentar converter indice para datetime
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
        return len(list(path.glob('*.parquet'))) == 0

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

    # =========================================================================
    # Coleta Incremental
    # =========================================================================

    def fetch_and_sync(
        self,
        filename: str,
        subdir: str,
        fetch_fn: Callable[[str | None], pd.DataFrame],
        frequency: str = 'daily',
        verbose: bool = True,
    ) -> tuple[pd.DataFrame, bool]:
        """
        Orquestra coleta incremental: verifica ultima data, busca dados, salva/append.

        Metodo generico para qualquer fonte de dados (BCB, IBGE, Bloomberg, etc).
        Centraliza a logica de decidir entre download completo ou incremental.

        Args:
            filename: Nome do arquivo (sem extensao)
            subdir: Subdiretorio em raw/
            fetch_fn: Funcao que recebe start_date e retorna DataFrame
                      - None: buscar historico completo
                      - 'YYYY-MM-DD': buscar a partir desta data
            frequency: Frequencia dos dados ('daily' ou 'monthly')
            verbose: Imprimir progresso

        Returns:
            (DataFrame com dados coletados, is_first_run)

        Example:
            def fetch(start_date):
                return client.get_data(code, start=start_date)

            df, is_first = data_manager.fetch_and_sync('selic', 'sgs/daily', fetch)
        """
        last_date = self.get_last_date(filename, subdir)
        is_first_run = last_date is None

        if is_first_run:
            start_date = None
        elif frequency == 'monthly':
            # Para series mensais, pular para o proximo mes
            next_month = (last_date.replace(day=1) + timedelta(days=32)).replace(day=1)
            start_date = next_month.strftime('%Y-%m-%d')
        else:
            start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')

        df = fetch_fn(start_date)

        if not df.empty:
            if is_first_run:
                self.save(df, filename, subdir, verbose=verbose)
            else:
                self.append(df, filename, subdir, verbose=verbose)

        return df, is_first_run

    # =========================================================================
    # Consolidacao
    # =========================================================================

    def consolidate(
        self,
        files: list[str] = None,
        output_filename: str = None,
        subdir: str = 'daily',
        save: bool = True,
        verbose: bool = False,
        add_source: bool = False,
    ) -> pd.DataFrame:
        """
        Consolida multiplos arquivos em um DataFrame.

        Args:
            files: Lista de nomes de arquivos (default: todos os arquivos do subdir)
            output_filename: Nome do arquivo consolidado (obrigatorio se save=True)
            subdir: Subdiretorio dentro de raw/
            save: Se True, salva em processed/
            verbose: Se True, imprime progresso
            add_source: Se True, adiciona coluna '_source' com nome do arquivo origem

        Returns:
            DataFrame consolidado
        """
        if files is None:
            files = self.list_files(subdir)

        if not files:
            if verbose:
                print(f"Nenhum arquivo para consolidar em {subdir}/")
            return pd.DataFrame()

        if verbose:
            print(f"Consolidando {len(files)} arquivos de {subdir}/...")

        dfs = []
        for filename in files:
            df = self.read(filename, subdir)
            if not df.empty:
                if add_source:
                    # Concatenar com coluna de origem
                    df = df.copy()
                    df['_source'] = filename
                    dfs.append(df)
                else:
                    # Usar filename como nome da coluna se tiver coluna 'value'
                    if 'value' in df.columns:
                        df = df.rename(columns={'value': filename})
                    dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        if add_source:
            # Concatenar verticalmente quando add_source=True
            result = pd.concat(dfs, ignore_index=True)
        else:
            # Juntar horizontalmente por indice
            result = dfs[0]
            for df in dfs[1:]:
                result = result.join(df, how='outer')
            result = result.sort_index()

        if save:
            if output_filename is None:
                raise ValueError("output_filename obrigatorio quando save=True")

            self.processed_path.mkdir(parents=True, exist_ok=True)
            filepath = self.processed_path / f"{output_filename}.parquet"
            result.to_parquet(
                filepath,
                engine='pyarrow',
                compression='snappy',
                index=True
            )
            if verbose:
                print(f"Salvo: {filepath.relative_to(self.base_path)}")

        if verbose:
            print(f"Total: {len(result):,} registros, {len(result.columns)} colunas")

        return result
