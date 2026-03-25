"""
Classe base para coletores de dados.

Fornece metodos utilitarios comuns para todos os collectors.
"""

from pathlib import Path

import pandas as pd

from adb.infra.persistence import DataManager
from adb.shared.utils import get_config


class BaseCollector:
    """
    Classe base para coletores de dados.

    Fornece:
    - Inicializacao padronizada com DataManager
    - Logging padronizado (_fetch_start, _fetch_result)
    - collect() template method (normalize -> start -> loop -> end)
    - status() generico com suporte a multi-subdir

    Subclasses devem definir:
    - _CONFIG: dict - configuracao de indicadores do provider
    - _TITLE: str - titulo para banner de coleta
    - default_subdir: str - subdiretorio padrao para operacoes
    - _collect_one() - logica de coleta de um indicador
    - _get_frequency_for_file() - frequencia de um indicador
    """

    _CONFIG: dict
    _TITLE: str
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
    # API Publica (Template Method)
    # =========================================================================

    def collect(
        self,
        indicators: list[str] | str = "all",
        start: str | None = None,
        end: str | None = None,
        save: bool = True,
        verbose: bool = True,
    ) -> None:
        """
        Coleta um ou mais indicadores.

        Template method: normaliza entrada, exibe banner, itera indicadores
        chamando _collect_one() em cada um, e exibe conclusao.

        Args:
            indicators: 'all', lista, ou string com indicador(es)
            start: Data inicial (formatos: '2020', '2020-01', '2020-01-01').
                   None = incremental desde ultima data salva.
            end: Data final (mesmos formatos). None = ate hoje.
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso
        """
        from adb.shared.utils import parse_date

        keys = self._normalize_indicators(indicators, self._CONFIG)
        parsed_start = parse_date(start) if start else None
        parsed_end = parse_date(end) if end else None

        self._start(
            title=self._TITLE,
            num_indicators=len(keys),
            subdir=self.default_subdir,
            check_first_run=True,
            verbose=verbose,
        )

        for key in keys:
            config = get_config(self._CONFIG, key)
            self._collect_one(
                key,
                config,
                start=parsed_start,
                end=parsed_end,
                save=save,
                verbose=verbose,
            )

        self._end(verbose=verbose)

    def _collect_one(
        self,
        key: str,
        config: dict,
        start: str | None,
        end: str | None,
        save: bool,
        verbose: bool,
    ) -> None:
        """
        Coleta um indicador individual.

        Subclasses devem implementar para chamar seu client especifico
        e delegar ao _persist().

        Args:
            key: Chave do indicador no _CONFIG
            config: Dict de configuracao do indicador
            start: Data inicial (ja parsed, ou None pra incremental)
            end: Data final (ja parsed, ou None pra ate hoje)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso
        """
        raise NotImplementedError("Subclasse deve implementar _collect_one")

    def _subdir_for(self, key: str) -> str:
        """
        Retorna subdiretorio para um indicador.

        Default: usa default_subdir. Override para subdirs dinamicos
        baseados em frequency (ex: SGS com daily/monthly).
        """
        return self.default_subdir

    # =========================================================================
    # Status
    # =========================================================================

    def status(self, subdir: str | None = None) -> pd.DataFrame:
        """
        Retorna status dos arquivos salvos com informacoes de saude.

        Agrega automaticamente todos os subdirs derivados do _CONFIG
        (ex: SGS agrega daily + monthly). Se subdir e passado, usa apenas esse.

        Args:
            subdir: Subdiretorio especifico (default: agrega todos do config)

        Returns:
            DataFrame com status de cada arquivo incluindo cobertura e gaps
        """
        if subdir:
            return self._status_for_subdir(subdir)

        # Derivar subdirs unicos do config
        subdirs = {self._subdir_for(key) for key in self._CONFIG}

        dfs = []
        for sd in sorted(subdirs):
            df = self._status_for_subdir(sd)
            if not df.empty:
                dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        return pd.concat(dfs, ignore_index=True)

    def _status_for_subdir(self, subdir: str) -> pd.DataFrame:
        """Retorna status dos arquivos em um subdiretorio especifico."""
        from adb.infra.persistence.validation import DataValidator

        files = self.data_manager.list_files(subdir)

        if not files:
            return pd.DataFrame()

        status_data = []

        with DataValidator(self.data_path) as validator:
            for filename in files:
                frequency = self._get_frequency_for_file(filename)
                if frequency is None:
                    continue

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

    def _persist(
        self,
        fetch_fn,
        filename: str,
        name: str,
        subdir: str,
        frequency: str,
        start: str | None = None,
        end: str | None = None,
        save: bool = True,
        verbose: bool = True,
    ) -> None:
        """
        Busca dados e persiste em disco (save ou append).

        Suporta coleta incremental: se start nao e fornecido e o arquivo
        existe, calcula start a partir da ultima data salva.

        Args:
            fetch_fn: Funcao(start_date, end_date) -> DataFrame
            filename: Nome do arquivo (sem extensao)
            name: Nome para exibicao
            subdir: Subdiretorio dentro de data/
            frequency: 'daily', 'monthly' ou 'quarterly'
            start: Data inicial (None = incremental desde ultima data)
            end: Data final (None = ate hoje)
            save: Se True, persiste em Parquet
            verbose: Se True, imprime progresso
        """
        # 1. Determinar start (incremental se nao explicito)
        effective_start = start
        if effective_start is None and save:
            last_date = self.data_manager.get_last_date(filename, subdir)
            if last_date is not None:
                effective_start = self._next_date(last_date, frequency)

        is_first_run = not self.data_manager.get_file_path(filename, subdir).exists()

        # 2. Fetch
        self._fetch_start(name, effective_start, verbose)
        try:
            df = fetch_fn(effective_start, end)
        except Exception as e:
            self.logger.error(f"Fetch error for {name}: {e}")
            self._fetch_result(name, 0, verbose)
            return

        # 3. Persist
        if not df.empty and save:
            if is_first_run:
                self.data_manager.save(df, filename, subdir, verbose=verbose)
            else:
                self.data_manager.append(df, filename, subdir, verbose=verbose)

        self._fetch_result(name, len(df), verbose)
