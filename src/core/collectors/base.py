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

    def __init__(self, data_path: Path = None):
        """
        Inicializa o coletor base.

        Args:
            data_path: Caminho para diretorio data/ (opcional, usa DATA_PATH se None)
        """
        from core.config import DATA_PATH
        self.data_path = Path(data_path) if data_path else DATA_PATH
        self.data_manager = DataManager(self.data_path)

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
            metadata = self.data_manager.get_metadata(filename, subdir)
            
            if metadata:
                status_data.append(metadata)
            else:
                 # Fallback apenas se get_metadata falhar ou arquivo vazio
                status_data.append({
                    'arquivo': filename,
                    'subdir': subdir,
                    'registros': 0,
                    'colunas': 0,
                    'primeira_data': None,
                    'ultima_data': None,
                    'status': 'Erro/Vazio',
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
            total = 0
            for res in results.values():
                if isinstance(res, int):
                    total += res
                elif hasattr(res, '__len__'):
                    total += len(res)
            print(f"Coleta concluida! Total: {total:,} registros")
        else:
            print("Coleta concluida!")

        print("=" * 70)


    def _calculate_start_date(self, last_date: pd.Timestamp | None, frequency: str) -> str | None:
        """Calcula data de inicio baseada na ultima data salva."""
        from datetime import timedelta
        
        # Trata None e pd.NaT (Not-a-Time) como ausencia de dados
        if last_date is None or pd.isna(last_date):
            return None
            
        if frequency == 'monthly':
            # Proximo mes (primeiro dia)
            next_month = (last_date.replace(day=1) + timedelta(days=32)).replace(day=1)
            return next_month.strftime('%Y-%m-%d')
        else:
            # Proximo dia
            return (last_date + timedelta(days=1)).strftime('%Y-%m-%d')

    def _collect_with_sync(
        self,
        fetch_fn,
        filename: str,
        name: str,
        subdir: str,
        frequency: str = 'daily',
        save: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Orquestra coleta incremental: verifica ultima data, busca dados, salva/append.
        """
        # 1. Determinar data de inicio
        is_first_run = True
        start_date = None
        
        if save and frequency:
            last_date = self.data_manager.get_last_date(filename, subdir)
            start_date = self._calculate_start_date(last_date, frequency)
            is_first_run = last_date is None

        # 2. Wrapper de log
        def fetch_with_log(date_param):
            self._log_fetch_start(name, date_param, verbose)
            return fetch_fn(date_param)

        # 3. Executar fetch
        try:
            df = fetch_with_log(start_date)
        except Exception as e:
            print(f"  Erro ao buscar dados: {e}")
            return pd.DataFrame()

        # 4. Salvar resultados
        if not df.empty and save:
            if is_first_run:
                self.data_manager.save(df, filename, subdir, verbose=verbose)
            else:
                self.data_manager.append(df, filename, subdir, verbose=verbose)

        # 5. Log final
        self._log_fetch_result(name, len(df), verbose)

        return df
