"""
Coletor de expectativas do BCB (Relatorio Focus).

Orquestra a coleta de dados de expectativas com flexibilidade de parametros.
Usa DataManager para persistencia (DRY).
"""

from pathlib import Path
import pandas as pd

from .client import ExpectationsClient
from .indicators import EXPECTATIONS_CONFIG, get_indicator_config
from data import DataManager


class ExpectationsCollector:
    """
    Orquestrador de coleta de expectativas do BCB.

    Oferece tres niveis de uso:
    1. collect_endpoint() - Controle total, usuario define tudo
    2. collect_indicator() - Usa config predefinida com override opcional
    3. collect_all() - Automacao completa
    """

    def __init__(self, data_path: Path):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho base para diretorio data/
        """
        self.data_path = Path(data_path)
        self.client = ExpectationsClient()
        self.data_manager = DataManager(data_path)

    # =========================================================================
    # NIVEL 1: Controle Total
    # =========================================================================

    def collect_endpoint(
        self,
        endpoint: str,
        filename: str,
        indicator: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = None,
        subdir: str = 'expectations',
        save: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Coleta dados de um endpoint com controle total.

        Args:
            endpoint: Chave do endpoint ('top5_anuais', 'selic', etc)
            filename: Nome do arquivo para salvar (sem extensao)
            indicator: Filtrar por indicador (ex: 'IPCA')
            start_date: Data inicial 'YYYY-MM-DD'
            end_date: Data final 'YYYY-MM-DD'
            limit: Limite de registros (None = sem limite)
            subdir: Subdiretorio dentro de raw/ (default: 'expectations')
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            DataFrame com dados coletados
        """
        if verbose:
            print(f"Coletando: {endpoint}", end="")
            if indicator:
                print(f" [{indicator}]", end="")
            print("...")

        df = self.client.query(
            endpoint_key=endpoint,
            indicator=indicator,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        if df.empty:
            if verbose:
                print(f"  Nenhum dado retornado")
            return df

        if verbose:
            print(f"  {len(df):,} registros coletados")

        if save:
            self.data_manager.save(
                df, filename, subdir,
                metadata={'endpoint': endpoint, 'indicator': indicator},
                verbose=verbose,
            )

        return df

    # =========================================================================
    # NIVEL 2: Config Predefinida
    # =========================================================================

    def collect_indicator(
        self,
        key: str,
        filename: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = None,
        subdir: str = 'expectations',
        save: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Coleta um indicador usando configuracao predefinida.

        Args:
            key: Chave do indicador em EXPECTATIONS_CONFIG
            filename: Nome do arquivo (default: usa key)
            start_date: Data inicial (override)
            end_date: Data final (override)
            limit: Limite de registros (override)
            subdir: Subdiretorio dentro de raw/
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            DataFrame com dados coletados
        """
        config = get_indicator_config(key)

        return self.collect_endpoint(
            endpoint=config['endpoint'],
            filename=filename or key,
            indicator=config['indicator'],
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            subdir=subdir,
            save=save,
            verbose=verbose,
        )

    # =========================================================================
    # NIVEL 3: Automatico
    # =========================================================================

    def collect_all(
        self,
        config: dict = None,
        subdir: str = 'expectations',
        start_date: str = None,
        limit: int = None,
        save: bool = True,
        verbose: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Coleta todos os indicadores da configuracao.

        Args:
            config: Dict de configuracao (default: EXPECTATIONS_CONFIG)
            subdir: Subdiretorio dentro de raw/
            start_date: Data inicial para todos (opcional)
            limit: Limite de registros para todos (opcional)
            save: Se True, salva cada indicador em Parquet
            verbose: Se True, imprime progresso

        Returns:
            Dict {key: DataFrame} com dados coletados
        """
        if config is None:
            config = EXPECTATIONS_CONFIG

        if verbose:
            print("=" * 70)
            print("COLETA DE EXPECTATIVAS DO BCB")
            print("=" * 70)
            print(f"Indicadores a coletar: {len(config)}")
            print()

        results = {}
        for key in config.keys():
            df = self.collect_indicator(
                key=key,
                filename=key,
                start_date=start_date,
                limit=limit,
                subdir=subdir,
                save=save,
                verbose=verbose,
            )
            results[key] = df
            if verbose:
                print()

        if verbose:
            print("=" * 70)
            total = sum(len(df) for df in results.values())
            print(f"Coleta concluida! Total: {total:,} registros")
            print("=" * 70)

        return results

    # =========================================================================
    # Consolidacao
    # =========================================================================

    def consolidate(
        self,
        files: list[str] = None,
        output_filename: str = 'expectations_consolidated',
        subdir: str = 'expectations',
        save: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Consolida multiplos arquivos em um DataFrame.

        Args:
            files: Lista de nomes de arquivos (default: todos os arquivos)
            output_filename: Nome do arquivo consolidado
            subdir: Subdiretorio dentro de raw/
            save: Se True, salva em processed/
            verbose: Se True, imprime progresso

        Returns:
            DataFrame consolidado
        """
        if files is None:
            files = self.data_manager.list_files(subdir)

        if not files:
            if verbose:
                print("Nenhum arquivo para consolidar")
            return pd.DataFrame()

        if verbose:
            print(f"Consolidando {len(files)} arquivos...")

        dfs = []
        for filename in files:
            df = self.data_manager.read(filename, subdir)
            if not df.empty:
                df['_source'] = filename
                dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        consolidated = pd.concat(dfs, ignore_index=True)

        if save:
            output_dir = self.data_path / 'processed'
            output_dir.mkdir(parents=True, exist_ok=True)

            filepath = output_dir / f"{output_filename}.parquet"
            consolidated.to_parquet(
                filepath,
                engine='pyarrow',
                compression='snappy',
                index=False,
            )
            if verbose:
                print(f"Salvo: {filepath.relative_to(self.data_path)}")

        if verbose:
            print(f"Total: {len(consolidated):,} registros")

        return consolidated

    # =========================================================================
    # Utilitarios (delegam para DataManager)
    # =========================================================================

    def save(
        self,
        df: pd.DataFrame,
        filename: str,
        subdir: str = 'expectations',
        **kwargs
    ):
        """Delega para DataManager.save()"""
        return self.data_manager.save(df, filename, subdir, **kwargs)

    def read(
        self,
        filename: str,
        subdir: str = 'expectations',
    ) -> pd.DataFrame:
        """Delega para DataManager.read()"""
        return self.data_manager.read(filename, subdir)

    def list_files(self, subdir: str = 'expectations') -> list[str]:
        """Delega para DataManager.list_files()"""
        return self.data_manager.list_files(subdir)

    def get_status(self, subdir: str = 'expectations') -> pd.DataFrame:
        """
        Retorna status dos arquivos salvos.

        Args:
            subdir: Subdiretorio dentro de raw/

        Returns:
            DataFrame com status de cada arquivo
        """
        files = self.data_manager.list_files(subdir)

        if not files:
            return pd.DataFrame()

        status_data = []
        for filename in files:
            df = self.data_manager.read(filename, subdir)

            if df.empty:
                status_data.append({
                    'arquivo': filename,
                    'registros': 0,
                    'colunas': 0,
                    'status': 'Vazio',
                })
            else:
                # Tentar identificar range de datas
                data_col = 'Data' if 'Data' in df.columns else None
                primeira_data = None
                ultima_data = None

                if data_col and pd.api.types.is_datetime64_any_dtype(df[data_col]):
                    primeira_data = df[data_col].min()
                    ultima_data = df[data_col].max()

                status_data.append({
                    'arquivo': filename,
                    'registros': len(df),
                    'colunas': len(df.columns),
                    'primeira_data': primeira_data,
                    'ultima_data': ultima_data,
                    'status': 'OK',
                })

        return pd.DataFrame(status_data)
