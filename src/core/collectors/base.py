"""
Classe base para coletores de dados.

Fornece metodos utilitarios comuns para todos os collectors.
"""

from pathlib import Path
import pandas as pd

from core.data import DataManager


class BaseCollector:
    """
    Classe base para coletores de dados.

    Fornece:
    - Inicializacao padronizada com DataManager
    - Logging padronizado (_log_fetch_start, _log_fetch_result)
    - get_status() generico baseado em arquivos

    Subclasses devem definir:
    - default_subdir: str - subdiretorio padrao para operacoes
    - default_consolidate_subdirs: list[str] - subdiretorios para consolidacao

    Subclasses podem sobrescrever:
    - get_status() - para logica especifica (ex: CAGED usa periodos)
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

    # =========================================================================
    # Helpers para Collectors (reduz duplicacao)
    # =========================================================================

    def _normalize_indicators_list(
        self,
        indicators: list[str] | str,
        config: dict
    ) -> list[str]:
        """
        Normaliza entrada de indicadores para lista.

        Args:
            indicators: 'all', string unico, ou lista
            config: Dicionario de configuracao (ex: SGS_CONFIG)

        Returns:
            Lista de chaves de indicadores
        """
        if indicators == 'all':
            return list(config.keys())
        elif isinstance(indicators, str):
            return [indicators]
        else:
            return list(indicators)

    def _normalize_subdirs_list(
        self,
        subdirs: list[str] | str | None
    ) -> list[str]:
        """
        Normaliza entrada de subdiretorios para lista.

        Args:
            subdirs: None (usa default), string unico, ou lista

        Returns:
            Lista de subdiretorios
        """
        if subdirs is None:
            return self.default_consolidate_subdirs
        elif isinstance(subdirs, str):
            return [subdirs]
        else:
            return list(subdirs)

    def _log_collect_start(
        self,
        title: str,
        num_indicators: int,
        subdir: str = None,
        check_first_run: bool = False,
        verbose: bool = True
    ):
        """
        Loga inicio de coleta com banner padronizado.

        Args:
            title: Titulo principal (ex: "BACEN - Sistema Gerenciador de Series")
            num_indicators: Numero de indicadores a coletar
            subdir: Subdiretorio para checar first_run (opcional)
            check_first_run: Se True, mostra "PRIMEIRA EXECUCAO" vs "ATUALIZACAO"
            verbose: Se False, nao imprime nada
        """
        if not verbose:
            return

        print("=" * 70)

        # Se pediu check de primeira execucao
        if check_first_run and subdir:
            is_first = self.data_manager.is_first_run(subdir)
            if is_first:
                print("PRIMEIRA EXECUCAO - Download de Historico Completo")
            else:
                print("ATUALIZACAO INCREMENTAL")
            print("=" * 70)

        print(title)
        print("=" * 70)
        print(f"Indicadores a coletar: {num_indicators}")
        print()

    def _log_collect_end(
        self,
        results: dict = None,
        verbose: bool = True
    ):
        """
        Loga conclusao de coleta com banner padronizado.

        Args:
            results: Dict {key: DataFrame} com resultados (opcional)
                     Se fornecido, calcula e mostra total de registros
            verbose: Se False, nao imprime nada
        """
        if not verbose:
            return

        print("=" * 70)

        if results:
            total = sum(len(df) for df in results.values())
            print(f"Coleta concluida! Total: {total:,} registros")
        else:
            print("Coleta concluida!")

        print("=" * 70)

    def _log_consolidate_start(
        self,
        title: str = "CONSOLIDANDO DADOS",
        subdir: str = None,
        verbose: bool = True
    ):
        """
        Loga inicio de consolidacao com banner padronizado.

        Args:
            title: Titulo da consolidacao
            subdir: Subdiretorio sendo consolidado (opcional)
            verbose: Se False, nao imprime nada
        """
        if not verbose:
            return

        print("=" * 70)
        print(title)
        if subdir:
            print(f"Subdiretorio: {subdir}")
        print("=" * 70)
        print()

    def _save_parquet_to_processed(
        self,
        df: pd.DataFrame,
        filename: str,
        verbose: bool = True
    ) -> Path | None:
        """
        Salva DataFrame em processed_path como parquet.

        Args:
            df: DataFrame a salvar
            filename: Nome do arquivo (sem extensao .parquet)
            verbose: Se True, imprime caminho salvo

        Returns:
            Path do arquivo salvo, ou None se df vazio
        """
        if df.empty:
            return None

        self.data_manager.processed_path.mkdir(parents=True, exist_ok=True)
        filepath = self.data_manager.processed_path / f"{filename}.parquet"

        df.to_parquet(
            filepath,
            engine='pyarrow',
            compression='snappy',
            index=True
        )

        if verbose:
            rel_path = filepath.relative_to(self.data_manager.base_path)
            print(f"  Salvo: {rel_path}")

        return filepath

    def _collect_with_sync(
        self,
        fetch_fn,
        filename: str,
        name: str,
        subdir: str,
        frequency: str = None,
        save: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Template pattern para coleta com suporte a fetch_and_sync.

        Padroniza o fluxo:
        1. Criar wrapper de fetch_fn que faz log
        2. Usar fetch_and_sync se save=True
        3. Log resultado
        4. Retornar DataFrame

        Args:
            fetch_fn: Funcao(start_date) que retorna DataFrame
                      Recebe start_date automatico ou None
            filename: Nome do arquivo (sem extensao)
            name: Nome para logs
            subdir: Subdiretorio em raw/
            frequency: 'daily', 'monthly', etc (para fetch_and_sync)
            save: Se True, usa fetch_and_sync
        verbose: Se True, imprime logs

        Returns:
            DataFrame coletado
        """
        # Wrapper que adiciona logging
        def fetch_with_log(start_date: str | None) -> pd.DataFrame:
            self._log_fetch_start(name, start_date, verbose)
            return fetch_fn(start_date)

        # Fetch com ou sem sync
        if save and frequency:
            df, _ = self.data_manager.fetch_and_sync(
                filename=filename,
                subdir=subdir,
                fetch_fn=fetch_with_log,
                frequency=frequency,
                verbose=False,
            )
        else:
            df = fetch_with_log(None)

        # Log resultado
        self._log_fetch_result(name, len(df), verbose)

        return df
