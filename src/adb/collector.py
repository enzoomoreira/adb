"""Coletor generico de series temporais."""

from pathlib import Path

import pandas as pd

from adb.infra.storage import DataManager


class BaseCollector:
    """Coletor generico para series temporais.

    Recebe configuracao completa no construtor -- nao precisa de subclasses.
    O Explorer cria instancias passando _CONFIG, _TITLE, _CLIENT_CLASS, _SUBDIR_TEMPLATE.
    """

    def __init__(
        self,
        config: dict,
        title: str,
        client_class: type,
        subdir_template: str,
        data_path: Path | None = None,
    ) -> None:
        from adb.infra.config import get_settings
        from adb.infra.log import get_logger
        from adb.infra.storage import DisplayCallback
        from adb.display import get_display

        self._CONFIG = config
        self._TITLE = title
        self._SUBDIR_TEMPLATE = subdir_template
        self.client = client_class()

        self.data_path = Path(data_path) if data_path else get_settings().data_dir
        self.data_manager = DataManager(self.data_path, callback=DisplayCallback())
        self.logger = get_logger(self.__class__.__name__)
        self.display = get_display()
        self._collect_total = 0

    # =========================================================================
    # Resolucao de subdir e frequency
    # =========================================================================

    def _resolve_subdir(self, config: dict) -> str:
        """Resolve subdir via template + frequency do config."""
        if "{frequency}" in self._SUBDIR_TEMPLATE:
            frequency = config.get("frequency", "daily")
            return self._SUBDIR_TEMPLATE.format(frequency=frequency)
        return self._SUBDIR_TEMPLATE

    def _get_frequency_for_file(self, filename: str) -> str | None:
        """Retorna frequency do config para um indicador."""
        config = self._CONFIG.get(filename, {})
        return config.get("frequency")

    # =========================================================================
    # Display
    # =========================================================================

    def _fetch_start(
        self, name: str, start_date: str | None = None, verbose: bool = True
    ) -> None:
        self.display.set_verbose(verbose)
        self.display.fetch_start(name, start_date)
        self.logger.debug(f"Fetch start: {name}, since={start_date}")

    def _fetch_result(self, name: str, count: int, verbose: bool = True) -> None:
        self.display.set_verbose(verbose)
        self.display.fetch_result(count)
        self._collect_total += count
        if count:
            self.logger.info(f"Fetch OK: {name}, {count:,} registros")
        else:
            self.logger.warning(f"Fetch vazio: {name}")

    # =========================================================================
    # API Publica
    # =========================================================================

    def collect(
        self,
        indicators: list[str] | str = "all",
        start: str | None = None,
        end: str | None = None,
        save: bool = True,
        verbose: bool = True,
    ) -> None:
        """Coleta indicadores sequencialmente com incrementalidade."""
        from adb.utils import parse_date

        keys = self._normalize_indicators(indicators)
        parsed_start = parse_date(start) if start else None
        parsed_end = parse_date(end) if end else None

        # Usar primeiro subdir derivado para checar first_run
        first_subdir = self._resolve_subdir(self._CONFIG[keys[0]]) if keys else ""

        self._start(
            title=self._TITLE,
            num_indicators=len(keys),
            subdir=first_subdir,
            check_first_run=True,
            verbose=verbose,
        )

        for key in keys:
            config = self._CONFIG[key]
            self._collect_one(key, config, parsed_start, parsed_end, save, verbose)

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
        """Coleta um indicador via client.get_data(config, start, end)."""
        frequency = config.get("frequency", "daily")
        subdir = self._resolve_subdir(config)
        name = config.get("name") or config.get("indicator") or key

        def fetch(start_date: str | None, end_date: str | None) -> pd.DataFrame:
            return self.client.get_data(config, start_date, end_date)

        self._persist(
            fetch_fn=fetch,
            filename=key,
            name=name,
            subdir=subdir,
            frequency=frequency,
            start=start,
            end=end,
            save=save,
            verbose=verbose,
        )

    # =========================================================================
    # Status
    # =========================================================================

    def status(self, subdir: str | None = None) -> pd.DataFrame:
        """Retorna status dos arquivos salvos com metricas de saude."""
        if subdir:
            return self._status_for_subdir(subdir)

        subdirs = {self._resolve_subdir(cfg) for cfg in self._CONFIG.values()}

        dfs = []
        for sd in sorted(subdirs):
            df = self._status_for_subdir(sd)
            if not df.empty:
                dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        return pd.concat(dfs, ignore_index=True)

    def _status_for_subdir(self, subdir: str) -> pd.DataFrame:
        from adb.infra.validation import DataValidator

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

    # =========================================================================
    # Helpers internos
    # =========================================================================

    def _normalize_indicators(self, indicators: list[str] | str) -> list[str]:
        if indicators == "all":
            return list(self._CONFIG.keys())
        if isinstance(indicators, str):
            return [indicators]
        return list(indicators)

    def _start(
        self,
        title: str,
        num_indicators: int,
        subdir: str | None = None,
        check_first_run: bool = False,
        verbose: bool = True,
    ) -> None:
        self._collect_total = 0
        first_run = None
        if check_first_run and subdir:
            first_run = self.data_manager.is_first_run(subdir)

        self.display.set_verbose(verbose)
        self.display.banner(
            title=title,
            first_run=first_run,
            indicator_count=num_indicators,
        )
        self.logger.info(
            f"Coleta iniciada: {num_indicators} indicadores, "
            f"first_run={first_run}, subdir={subdir}"
        )

    def _end(self, verbose: bool = True) -> None:
        total = self._collect_total if self._collect_total > 0 else None
        self.display.set_verbose(verbose)
        self.display.end_banner(total=total)
        if total is not None:
            self.logger.info(f"Coleta concluida: {total:,} registros")
        else:
            self.logger.info("Coleta concluida")

    def _next_date(self, last_date: pd.Timestamp | None, frequency: str) -> str | None:
        """Calcula proxima data baseado na frequencia."""
        from datetime import timedelta

        if last_date is None or pd.isna(last_date):
            return None

        if frequency == "monthly":
            next_month = (last_date.replace(day=1) + timedelta(days=32)).replace(day=1)
            return next_month.strftime("%Y-%m-%d")
        elif frequency == "quarterly":
            quarter = (last_date.month - 1) // 3
            next_quarter_month = (quarter + 1) * 3 + 1
            if next_quarter_month > 12:
                return last_date.replace(
                    year=last_date.year + 1, month=1, day=1
                ).strftime("%Y-%m-%d")
            return last_date.replace(month=next_quarter_month, day=1).strftime(
                "%Y-%m-%d"
            )
        else:
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
        """Busca dados e persiste com incrementalidade."""
        effective_start = start
        if effective_start is None and save:
            last_date = self.data_manager.get_last_date(filename, subdir)
            if last_date is not None:
                effective_start = self._next_date(last_date, frequency)

        is_first_run = not self.data_manager.get_file_path(filename, subdir).exists()

        self._fetch_start(name, effective_start, verbose)
        try:
            df = fetch_fn(effective_start, end)
        except Exception as e:
            self.logger.error(f"Fetch error for {name}: {e}")
            self._fetch_result(name, 0, verbose)
            return

        if not df.empty and save:
            if is_first_run:
                self.data_manager.save(df, filename, subdir, verbose=verbose)
            else:
                self.data_manager.append(df, filename, subdir, verbose=verbose)

        self._fetch_result(name, len(df), verbose)
