"""
Classe base para coletores de dados.

Fornece metodos utilitarios comuns para todos os collectors.
"""

from pathlib import Path
import pandas as pd

from adb.core.data import DataManager
from adb.core.display import get_display
from adb.core.log import get_logger


class BaseCollector:
    """
    Classe base para coletores de dados.

    Fornece:
    - Inicializacao padronizada com DataManager
    - Logging padronizado (_fetch_start, _fetch_result)
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
        from adb.core.config import DATA_PATH
        self.data_path = Path(data_path) if data_path else DATA_PATH
        self.data_manager = DataManager(self.data_path)
        self.logger = get_logger(self.__class__.__name__)
        self.display = get_display()  # Display singleton para output visual
        self._collect_total = 0  # Acumulador para total de registros coletados

    # =========================================================================
    # Display (output visual ao usuario)
    # =========================================================================

    def _fetch_start(self, name: str, start_date: str = None, verbose: bool = True):
        """Exibe inicio de fetch de indicador (console + log tecnico)."""
        self.display.set_verbose(verbose)
        self.display.fetch_start(name, start_date)
        # Log tecnico sempre vai para arquivo
        self.logger.debug(f"Fetch start: {name}, since={start_date}")

    def _fetch_result(self, name: str, count: int, verbose: bool = True):
        """Exibe resultado de fetch de indicador (console + log tecnico)."""
        self.display.set_verbose(verbose)
        self.display.fetch_result(count)
        # Acumular total de registros
        self._collect_total += count
        # Log tecnico sempre vai para arquivo
        if count:
            self.logger.info(f"Fetch OK: {name}, {count:,} registros")
        else:
            self.logger.warning(f"Fetch vazio: {name}")

    def _info(self, message: str, verbose: bool = True):
        """Exibe mensagem informativa (console + log tecnico)."""
        self.display.set_verbose(verbose)
        self.display.info(message)
        self.logger.info(message)

    def _warning(self, message: str, verbose: bool = True):
        """Exibe warning (console + log tecnico)."""
        self.display.set_verbose(verbose)
        self.display.warning(message)
        self.logger.warning(message)

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

    def _normalize_indicators(
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


    def _start(
        self,
        title: str,
        num_indicators: int,
        subdir: str = None,
        check_first_run: bool = False,
        verbose: bool = True
    ):
        """
        Exibe banner de inicio de coleta (console + log tecnico).

        Args:
            title: Titulo principal (ex: "BACEN - Sistema Gerenciador de Series")
            num_indicators: Numero de indicadores a coletar
            subdir: Subdiretorio para checar first_run (opcional)
            check_first_run: Se True, mostra "PRIMEIRA EXECUCAO" vs "ATUALIZACAO"
            verbose: Se False, nao imprime no console
        """
        # Resetar acumulador de registros
        self._collect_total = 0

        # Determinar se e primeira execucao
        first_run = None
        if check_first_run and subdir:
            first_run = self.data_manager.is_first_run(subdir)

        # Display visual (console)
        self.display.set_verbose(verbose)
        self.display.banner(
            title=title,
            first_run=first_run,
            indicator_count=num_indicators,
        )

        # Log tecnico (arquivo)
        self.logger.info(
            f"Coleta iniciada: {num_indicators} indicadores, "
            f"first_run={first_run}, subdir={subdir}"
        )

    def _end(self, verbose: bool = True):
        """
        Exibe banner de conclusao de coleta (console + log tecnico).

        Usa total acumulado automaticamente via _fetch_result().

        Args:
            verbose: Se False, nao imprime no console
        """
        total = self._collect_total if self._collect_total > 0 else None

        # Display visual (console)
        self.display.set_verbose(verbose)
        self.display.end_banner(total=total)

        # Log tecnico (arquivo)
        if total is not None:
            self.logger.info(f"Coleta concluida: {total:,} registros")
        else:
            self.logger.info("Coleta concluida")


    def _next_date(self, last_date: pd.Timestamp | None, frequency: str) -> str | None:
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

    def _sync(
        self,
        fetch_fn,
        filename: str,
        name: str,
        subdir: str,
        frequency: str = 'daily',
        save: bool = True,
        verbose: bool = True,
    ) -> None:
        """
        Orquestra coleta incremental: verifica ultima data, busca dados, salva/append.
        
        Dados sao salvos diretamente em disco. Nao retorna DataFrame para evitar
        poluicao de output em notebooks (comportamento da API antiga collect()).
        """
        # 1. Determinar data de inicio
        is_first_run = True
        start_date = None
        
        if save and frequency:
            last_date = self.data_manager.get_last_date(filename, subdir)
            start_date = self._next_date(last_date, frequency)
            is_first_run = last_date is None

        # 2. Wrapper de log
        def fetch_with_log(date_param):
            self._fetch_start(name, date_param, verbose)
            return fetch_fn(date_param)

        # 3. Executar fetch
        try:
            df = fetch_with_log(start_date)
        except Exception as e:
            self.logger.error(f"Unexpected error during fetch for {name}: {e}")
            return pd.DataFrame()

        # 4. Salvar resultados
        if not df.empty and save:
            if is_first_run:
                self.data_manager.save(df, filename, subdir, verbose=verbose)
            else:
                self.data_manager.append(df, filename, subdir, verbose=verbose)

        # 5. Log final
        self._fetch_result(name, len(df), verbose)

        # Nao retorna df - dados ja salvos em disco
        # Evita poluicao de output no notebook (comportamento da API antiga)
