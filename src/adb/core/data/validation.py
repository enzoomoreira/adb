"""
Modulo de validacao de integridade de dados.

Usa cuallee para checks de qualidade e bizdays para calendario brasileiro (ANBIMA).
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path

import duckdb
import pandas as pd
from bizdays import Calendar


class HealthStatus(Enum):
    """Status de saude dos dados."""
    OK = "ok"           # Dados completos e atualizados
    STALE = "stale"     # Dados desatualizados
    GAPS = "gaps"       # Dados com lacunas
    MISSING = "missing" # Arquivo nao existe


class Frequency(Enum):
    """Frequencias de dados suportadas."""
    DAILY = "daily"         # Dias uteis (ANBIMA)
    MONTHLY = "monthly"     # Mensal
    QUARTERLY = "quarterly" # Trimestral


@dataclass
class Gap:
    """Representa uma lacuna nos dados."""
    start: date
    end: date
    expected_records: int


@dataclass
class HealthReport:
    """Relatorio de saude dos dados."""
    status: HealthStatus
    first_date: date | None = None
    last_date: date | None = None
    expected_records: int = 0
    actual_records: int = 0
    coverage: float = 0.0  # 0-100
    gaps: list[Gap] = field(default_factory=list)
    stale_days: int = 0
    cuallee_results: dict = field(default_factory=dict)


class DataValidator:
    """
    Validador de integridade de dados.

    Usa bizdays para calendario brasileiro (ANBIMA) e cuallee para checks
    de qualidade de dados.

    Exemplo:
        >>> with DataValidator() as validator:
        ...     health = validator.get_health('selic', 'bacen/sgs/daily', 'daily')
        ...     print(health.status)  # HealthStatus.OK
        ...     print(health.coverage)  # 98.5
    """

    # Limites para considerar dados como desatualizados (stale)
    STALE_THRESHOLD = {
        Frequency.DAILY: 3,      # 3 dias uteis
        Frequency.MONTHLY: 45,   # 45 dias
        Frequency.QUARTERLY: 95, # 95 dias (~3 meses)
    }

    # Limiar minimo de cobertura para considerar dados OK
    COVERAGE_THRESHOLD = 95.0

    def __init__(self, base_path: Path = None):
        """
        Inicializa o validador.

        Args:
            base_path: Caminho base para dados. Default usa DATA_PATH.
        """
        from adb.core.config import DATA_PATH
        self.base_path = Path(base_path) if base_path else DATA_PATH
        self.raw_path = self.base_path / 'raw'
        self._conn = duckdb.connect()

        # Calendario ANBIMA para dias uteis brasileiros
        try:
            self._calendar = Calendar.load('ANBIMA')
        except Exception:
            # Calendario fora do range ou erro ao carregar - usa fallback weekdays
            self._calendar = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit - fecha conexao."""
        self.close()

    def close(self):
        """Fecha conexao DuckDB."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def get_health(
        self,
        filename: str,
        subdir: str,
        frequency: str | Frequency,
    ) -> HealthReport:
        """
        Analisa saude dos dados de um arquivo.

        Args:
            filename: Nome do arquivo (sem extensao .parquet)
            subdir: Subdiretorio dentro de raw/
            frequency: Frequencia dos dados ('daily', 'monthly', 'quarterly')

        Returns:
            HealthReport com status, cobertura, gaps, etc.
        """
        filepath = self.raw_path / subdir / f"{filename}.parquet"

        # Arquivo nao existe
        if not filepath.exists():
            return HealthReport(status=HealthStatus.MISSING)

        # Normalizar frequency para Enum
        if isinstance(frequency, str):
            frequency = Frequency(frequency)

        # Verificar se tem coluna date (alguns datasets usam outras colunas)
        if not self._has_date_column(filepath):
            # Sem validacao temporal - retorna status basico
            count = self._get_row_count(filepath)
            return HealthReport(
                status=HealthStatus.OK,
                actual_records=count,
                coverage=100.0,
            )

        # 1. Checks basicos via cuallee
        cuallee_results = self._run_cuallee_checks(filepath)

        # 2. Extrair datas do arquivo
        actual_dates = self._get_actual_dates(filepath)
        if not actual_dates:
            return HealthReport(status=HealthStatus.MISSING)

        first_date = min(actual_dates)
        last_date = max(actual_dates)

        # 3. Gerar datas esperadas baseado na frequencia
        expected_dates = self._generate_expected_dates(first_date, date.today(), frequency)

        # 4. Calcular gaps (datas faltantes)
        missing_dates = expected_dates - actual_dates
        gaps = self._dates_to_gaps(sorted(missing_dates), frequency)

        # 5. Calcular metricas
        if expected_dates:
            coverage = len(actual_dates) / len(expected_dates) * 100
            # Cap coverage at 100% (pode exceder se calendario nao cobre periodo antigo)
            coverage = min(coverage, 100.0)
        else:
            coverage = 0
        stale_days = self._calculate_staleness(last_date, frequency)
        # Stale nao pode ser negativo (dados do futuro)
        stale_days = max(stale_days, 0)

        # 6. Determinar status
        status = self._determine_status(coverage, stale_days, frequency)

        return HealthReport(
            status=status,
            first_date=first_date,
            last_date=last_date,
            expected_records=len(expected_dates),
            actual_records=len(actual_dates),
            coverage=round(coverage, 2),
            gaps=gaps,
            stale_days=stale_days,
            cuallee_results=cuallee_results,
        )

    def _has_date_column(self, filepath: Path) -> bool:
        """Verifica se arquivo tem coluna ou indice 'date'."""
        try:
            # DuckDB le indice como coluna automaticamente
            sql = f"DESCRIBE SELECT * FROM '{filepath}' LIMIT 0"
            schema = self._conn.execute(sql).df()
            return 'date' in schema['column_name'].values
        except Exception:
            return False

    def _get_row_count(self, filepath: Path) -> int:
        """Retorna contagem de linhas do arquivo."""
        try:
            sql = f"SELECT COUNT(*) FROM '{filepath}'"
            return self._conn.execute(sql).fetchone()[0]
        except Exception:
            return 0

    def _run_cuallee_checks(self, filepath: Path) -> dict:
        """
        Executa checks de qualidade via cuallee.

        Verifica:
        - is_complete: coluna date sem nulos
        - is_unique: sem datas duplicadas
        """
        from cuallee import Check, CheckLevel

        try:
            # Ler apenas coluna date via DuckDB (mais eficiente que pd.read_parquet)
            sql = f"SELECT date FROM '{filepath}'"
            df = self._conn.execute(sql).df()

            if df.empty or 'date' not in df.columns:
                return {'passed': True, 'details': []}

            check = Check(CheckLevel.WARNING, "HealthCheck")
            check.is_complete("date")  # Sem nulos
            check.is_unique("date")    # Sem duplicatas

            result = check.validate(df)

            return {
                'passed': result['status'].eq('PASS').all(),
                'details': result.to_dict('records'),
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _get_actual_dates(self, filepath: Path) -> set[date]:
        """Extrai datas unicas do arquivo via DuckDB."""
        try:
            sql = f"SELECT DISTINCT CAST(date AS DATE) as d FROM '{filepath}'"
            result = self._conn.execute(sql).fetchall()
            return {row[0] for row in result if row[0]}
        except Exception:
            return set()

    def _generate_expected_dates(
        self,
        start: date,
        end: date,
        frequency: Frequency,
    ) -> set[date]:
        """
        Gera conjunto de datas esperadas baseado na frequencia.

        Args:
            start: Data inicial
            end: Data final
            frequency: Frequencia dos dados

        Returns:
            Set de datas esperadas
        """
        if frequency == Frequency.DAILY:
            # Dias uteis brasileiros (calendario ANBIMA)
            if self._calendar:
                try:
                    return set(self._calendar.seq(start, end))
                except Exception:
                    # Calendario fora do range - usar fallback
                    pass
            # Fallback: dias de semana (seg-sex)
            return self._generate_weekdays(start, end)

        elif frequency == Frequency.MONTHLY:
            # Primeiro dia de cada mes usando pandas date_range
            start_adjusted = start.replace(day=1)
            return set(pd.date_range(start_adjusted, end, freq='MS').date)

        elif frequency == Frequency.QUARTERLY:
            # Primeiro dia de cada trimestre (jan, abr, jul, out)
            # Ajustar start para inicio do trimestre mais proximo
            quarter_months = [1, 4, 7, 10]
            current = start.replace(day=1)
            while current.month not in quarter_months:
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            return set(pd.date_range(current, end, freq='QS').date)

        return set()

    def _generate_weekdays(self, start: date, end: date) -> set[date]:
        """
        Gera dias de semana (seg-sex) como fallback quando calendario ANBIMA fora do range.

        Args:
            start: Data inicial
            end: Data final

        Returns:
            Set de datas (apenas dias uteis aproximados, sem considerar feriados)
        """
        # pd.bdate_range gera business days (seg-sex) automaticamente
        return set(pd.bdate_range(start, end).date)

    def _dates_to_gaps(
        self,
        missing_dates: list[date],
        frequency: Frequency,
    ) -> list[Gap]:
        """
        Agrupa datas faltantes em gaps contiguos.

        Args:
            missing_dates: Lista ordenada de datas faltantes
            frequency: Frequencia dos dados

        Returns:
            Lista de Gap objects
        """
        if not missing_dates:
            return []

        gaps = []
        gap_start = missing_dates[0]
        gap_count = 1
        prev_date = missing_dates[0]

        for current_date in missing_dates[1:]:
            # Verifica se e contiguo baseado na frequencia
            if self._is_contiguous(prev_date, current_date, frequency):
                gap_count += 1
            else:
                # Fecha gap atual e inicia novo
                gaps.append(Gap(
                    start=gap_start,
                    end=prev_date,
                    expected_records=gap_count,
                ))
                gap_start = current_date
                gap_count = 1
            prev_date = current_date

        # Adicionar ultimo gap
        gaps.append(Gap(
            start=gap_start,
            end=prev_date,
            expected_records=gap_count,
        ))

        return gaps

    def _is_contiguous(
        self,
        prev_date: date,
        current_date: date,
        frequency: Frequency,
    ) -> bool:
        """Verifica se duas datas sao contiguas para a frequencia."""
        if frequency == Frequency.DAILY:
            # Proximo dia util
            if self._calendar:
                try:
                    next_biz = self._calendar.offset(prev_date, 1)
                    return current_date == next_biz
                except Exception:
                    pass
            # Fallback: considera contiguo se diferenca <= 5 dias
            return (current_date - prev_date).days <= 5

        elif frequency == Frequency.MONTHLY:
            # Proximo mes
            if prev_date.month == 12:
                expected = prev_date.replace(year=prev_date.year + 1, month=1)
            else:
                expected = prev_date.replace(month=prev_date.month + 1)
            return current_date == expected

        elif frequency == Frequency.QUARTERLY:
            # Proximo trimestre (3 meses)
            month = prev_date.month + 3
            year = prev_date.year
            if month > 12:
                month -= 12
                year += 1
            expected = prev_date.replace(year=year, month=month)
            return current_date == expected

        return False

    def _calculate_staleness(self, last_date: date, frequency: Frequency) -> int:
        """
        Calcula dias desde ultima atualizacao.

        Para dados diarios, usa dias uteis (ANBIMA) se disponivel.
        Para outros, usa dias corridos.
        """
        today = date.today()

        if frequency == Frequency.DAILY and self._calendar:
            try:
                return self._calendar.bizdays(last_date, today)
            except Exception:
                pass
        # Fallback: dias corridos
        return (today - last_date).days

    def _determine_status(
        self,
        coverage: float,
        stale_days: int,
        frequency: Frequency,
    ) -> HealthStatus:
        """Determina status de saude baseado em cobertura e staleness."""
        threshold = self.STALE_THRESHOLD.get(frequency, 7)

        if coverage < self.COVERAGE_THRESHOLD:
            return HealthStatus.GAPS
        elif stale_days > threshold:
            return HealthStatus.STALE
        else:
            return HealthStatus.OK
