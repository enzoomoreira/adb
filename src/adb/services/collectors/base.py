"""
Classe base para coletores de dados.

Fornece metodos utilitarios comuns para todos os collectors.
"""

from pathlib import Path
import pandas as pd

from adb.infra.persistence import DataManager


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
    - get_status() - para logica especifica de cada provider
    """

    default_subdir: str = ""

    def __init__(self, data_path: Path | None = None):
        """
        Inicializa o coletor base.

        Args:
            data_path: Caminho para diretorio data/ (opcional, usa DATA_PATH se None)
        """
        from adb.infra.config import get_settings

        self.data_path = Path(data_path) if data_path else get_settings().data_dir

        # DataManager com callback para feedback visual
        from adb.infra.persistence.storage import DisplayCallback

        self.data_manager = DataManager(self.data_path, callback=DisplayCallback())

        # Imports lazy - so carrega quando collector e instanciado
        from adb.infra.log import get_logger
        from adb.ui.display import get_display

        self.logger = get_logger(self.__class__.__name__)
        self.display = get_display()  # Display singleton para output visual
        self._collect_total = 0  # Acumulador para total de registros coletados

    # =========================================================================
    # Display (output visual ao usuario)
    # =========================================================================

    def _fetch_start(
        self, name: str, start_date: str | None = None, verbose: bool = True
    ):
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

    def get_status(self, subdir: str | None = None) -> pd.DataFrame:
        """
        Retorna status dos arquivos salvos com informacoes de saude.

        Usa DataValidator para calcular cobertura, gaps e status real dos dados.

        Args:
            subdir: Subdiretorio (default: default_subdir)

        Returns:
            DataFrame com status de cada arquivo incluindo cobertura e gaps

        Raises:
            ValueError: Se frequencia do indicador nao estiver configurada.
        """
        from adb.infra.persistence.validation import DataValidator

        subdir = subdir or self.default_subdir
        files = self.data_manager.list_files(subdir)

        if not files:
            return pd.DataFrame()

        status_data = []

        with DataValidator(self.data_path) as validator:
            for filename in files:
                # Obter frequencia do indicador (subclasses devem implementar)
                frequency = self._get_frequency_for_file(filename)
                if frequency is None:
                    raise ValueError(
                        f"Frequencia desconhecida para '{filename}'. "
                        f"Adicione 'frequency' na configuracao do indicador."
                    )

                # Validar saude dos dados
                health = validator.get_health(filename, subdir, frequency)

                status_data.append(
                    {
                        "arquivo": filename,
                        "subdir": subdir,
                        "registros": health.actual_records,
                        "primeira_data": health.first_date,
                        "ultima_data": health.last_date,
                        "cobertura": health.coverage,
                        "gaps": len(health.gaps) if health.gaps else 0,
                        "status": health.status.value.upper(),
                    }
                )

        return pd.DataFrame(status_data)

    def _get_frequency_for_file(self, filename: str) -> str | None:
        """
        Retorna a frequencia de um indicador pelo nome do arquivo.

        Subclasses devem sobrescrever para retornar a frequencia correta
        baseada na configuracao do indicador.

        Args:
            filename: Nome do arquivo (sem extensao)

        Returns:
            'daily', 'monthly', 'quarterly' ou None se desconhecido
        """
        return None

    # =========================================================================
    # Helpers para Collectors (reduz duplicacao)
    # =========================================================================

    def _normalize_indicators(
        self, indicators: list[str] | str, config: dict
    ) -> list[str]:
        """
        Normaliza entrada de indicadores para lista.

        Args:
            indicators: 'all', string unico, ou lista
            config: Dicionario de configuracao (ex: SGS_CONFIG)

        Returns:
            Lista de chaves de indicadores
        """
        if indicators == "all":
            return list(config.keys())
        elif isinstance(indicators, str):
            return [indicators]
        else:
            return list(indicators)

    def _start(
        self,
        title: str,
        num_indicators: int,
        subdir: str | None = None,
        check_first_run: bool = False,
        verbose: bool = True,
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
        """
        Calcula data de inicio baseada na ultima data salva.

        Args:
            last_date: Ultima data presente nos dados
            frequency: 'daily', 'monthly' ou 'quarterly'

        Returns:
            Proxima data esperada em formato 'YYYY-MM-DD', ou None se last_date invalido
        """
        from datetime import timedelta

        # Trata None e pd.NaT (Not-a-Time) como ausencia de dados
        if last_date is None or pd.isna(last_date):
            return None

        if frequency == "monthly":
            # Proximo mes (primeiro dia)
            next_month = (last_date.replace(day=1) + timedelta(days=32)).replace(day=1)
            return next_month.strftime("%Y-%m-%d")

        elif frequency == "quarterly":
            # Proximo trimestre (primeiro dia de Jan, Abr, Jul, Out)
            quarter = (last_date.month - 1) // 3  # 0, 1, 2, 3
            next_quarter_month = (quarter + 1) * 3 + 1  # 4, 7, 10, 13
            if next_quarter_month > 12:
                return last_date.replace(
                    year=last_date.year + 1, month=1, day=1
                ).strftime("%Y-%m-%d")
            return last_date.replace(month=next_quarter_month, day=1).strftime(
                "%Y-%m-%d"
            )

        else:
            # daily - proximo dia
            return (last_date + timedelta(days=1)).strftime("%Y-%m-%d")

    def _sync(
        self,
        fetch_fn,
        filename: str,
        name: str,
        subdir: str,
        frequency: str = "daily",
        save: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame | None:
        """
        Orquestra coleta incremental: valida dados existentes, busca novos, salva/append.

        Usa DataValidator para verificar integridade dos dados existentes antes de
        determinar estrategia de coleta.

        Args:
            fetch_fn: Funcao que recebe start_date e retorna DataFrame
            filename: Nome do arquivo (sem extensao)
            name: Nome para exibicao
            subdir: Subdiretorio dentro de data/
            frequency: 'daily', 'monthly' ou 'quarterly'
            save: Se True, salva resultados em Parquet
            verbose: Se True, imprime progresso
        """
        from adb.infra.persistence.validation import DataValidator, HealthStatus

        # 1. Validar dados existentes
        with DataValidator(self.data_path) as validator:
            health = validator.get_health(filename, subdir, frequency)

        self.logger.debug(
            f"Health: {filename} - {health.status.value}, "
            f"coverage={health.coverage}%, stale={health.stale_days}d"
        )

        # 2. Determinar estrategia baseada no health check
        is_first_run = health.status == HealthStatus.MISSING
        start_date = None

        if not is_first_run and save:
            # Arquivo existe - calcular data de inicio
            if health.last_date:
                ts = pd.Timestamp(health.last_date)
                if isinstance(ts, pd.Timestamp):
                    start_date = self._next_date(ts, frequency)

        # 3. Wrapper de log
        def fetch_with_log(date_param):
            self._fetch_start(name, date_param, verbose)
            return fetch_fn(date_param)

        # 4. Executar fetch
        try:
            df = fetch_with_log(start_date)
        except Exception as e:
            self.logger.error(f"Unexpected error during fetch for {name}: {e}")
            return pd.DataFrame()

        # 5. Salvar resultados
        if not df.empty and save:
            if is_first_run:
                self.data_manager.save(df, filename, subdir, verbose=verbose)
            else:
                self.data_manager.append(df, filename, subdir, verbose=verbose)

        # 6. Log final
        self._fetch_result(name, len(df), verbose)

        # Nao retorna df - dados ja salvos em disco
        # Evita poluicao de output no notebook (comportamento da API antiga)
