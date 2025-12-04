"""
Gerenciador centralizado de dados para o projeto dados-bcb.

Fornece API flexivel para salvar, ler e consolidar dados em formato Parquet.
Usado por todos os modulos (SGS, Expectations, etc).
"""

from pathlib import Path
import pandas as pd
from datetime import datetime


class DataManager:
    """
    Gerenciador de dados Parquet para indicadores economicos.

    Oferece API flexivel onde o usuario pode escolher:
    - filename: nome do arquivo
    - subdir: subdiretorio dentro de raw/
    - format: formato do arquivo (parquet ou csv)
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
    # API FLEXIVEL (Principal)
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
        verbose: bool = False,
    ):
        """
        Adiciona novos dados a um arquivo existente (update incremental).

        Args:
            df: DataFrame com novos dados
            filename: Nome do arquivo
            subdir: Subdiretorio dentro de raw/
            verbose: Se True, imprime progresso
        """
        existing_df = self.read(filename, subdir)

        if existing_df.empty:
            self.save(df, filename, subdir, verbose=verbose)
            return

        combined = pd.concat([existing_df, df])
        combined = combined[~combined.index.duplicated(keep='last')]
        combined = combined.sort_index()

        # Preservar metadata existente
        combined.attrs = existing_df.attrs.copy()
        combined.attrs['last_update'] = datetime.now().isoformat()

        self.save(combined, filename, subdir, metadata=combined.attrs, verbose=verbose)

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
        return df.index.max()

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

    # =========================================================================
    # METODOS DE CONVENIENCIA (Compatibilidade com API antiga)
    # =========================================================================

    def save_indicator(
        self,
        df: pd.DataFrame,
        indicator_key: str,
        frequency: str,
        metadata: dict = None
    ):
        """
        Salva DataFrame de um indicador (wrapper de compatibilidade).

        Args:
            df: DataFrame com dados do indicador
            indicator_key: Identificador unico do indicador
            frequency: Frequencia dos dados ('daily', 'monthly', 'expectations')
            metadata: Dicionario com metadata adicional
        """
        self.save(df, filename=indicator_key, subdir=frequency, metadata=metadata)

    def read_indicator(self, indicator_key: str, frequency: str) -> pd.DataFrame:
        """
        Le dados de um indicador (wrapper de compatibilidade).

        Args:
            indicator_key: Identificador unico do indicador
            frequency: Frequencia dos dados

        Returns:
            DataFrame com dados do indicador
        """
        return self.read(filename=indicator_key, subdir=frequency)

    def append_indicator(
        self,
        new_df: pd.DataFrame,
        indicator_key: str,
        frequency: str
    ):
        """
        Adiciona novos dados a um indicador existente (wrapper de compatibilidade).

        Args:
            new_df: DataFrame com novos dados
            indicator_key: Identificador unico do indicador
            frequency: Frequencia dos dados
        """
        self.append(new_df, filename=indicator_key, subdir=frequency)

    def list_indicators(self, frequency: str) -> list[str]:
        """
        Lista indicadores disponiveis (wrapper de compatibilidade).

        Args:
            frequency: Frequencia dos dados

        Returns:
            Lista de nomes de indicadores
        """
        return self.list_files(subdir=frequency)

    def consolidate_daily(self) -> pd.DataFrame:
        """Consolida indicadores diarios (wrapper de compatibilidade)."""
        return self.consolidate(subdir='daily', save=False)

    def consolidate_monthly(self) -> pd.DataFrame:
        """Consolida indicadores mensais (wrapper de compatibilidade)."""
        return self.consolidate(subdir='monthly', save=False)

    # =========================================================================
    # METODOS INTERNOS
    # =========================================================================

    def _get_file_path(self, filename: str, subdir: str) -> Path:
        """
        Retorna o caminho do arquivo.

        Args:
            filename: Nome do arquivo
            subdir: Subdiretorio

        Returns:
            Path do arquivo Parquet
        """
        return self.raw_path / subdir / f"{filename}.parquet"
