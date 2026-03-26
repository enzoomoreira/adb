"""Testes para adb.infra.validation (DataValidator, HealthReport)."""

from datetime import date
from pathlib import Path

import duckdb
import pandas as pd

from adb.infra.validation import (
    DataValidator,
    Frequency,
    Gap,
    HealthReport,
    HealthStatus,
)


def _save_parquet(df: pd.DataFrame, filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    duckdb.register("_test_df", df)
    try:
        duckdb.sql(
            f"COPY _test_df TO '{filepath}' (FORMAT 'parquet', COMPRESSION 'snappy')"
        )
    finally:
        duckdb.unregister("_test_df")


# =========================================================================
# _determine_status
# =========================================================================


class TestDetermineStatus:
    """Regras de negocio para determinacao de status."""

    def test_ok_when_high_coverage_and_fresh(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            status = v._determine_status(
                coverage=98.0, stale_days=1, frequency=Frequency.DAILY
            )
            assert status == HealthStatus.OK

    def test_gaps_when_low_coverage(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            status = v._determine_status(
                coverage=80.0, stale_days=0, frequency=Frequency.DAILY
            )
            assert status == HealthStatus.GAPS

    def test_stale_when_daily_exceeds_threshold(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            # DAILY threshold = 3 business days
            status = v._determine_status(
                coverage=99.0, stale_days=5, frequency=Frequency.DAILY
            )
            assert status == HealthStatus.STALE

    def test_stale_monthly_threshold(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            # MONTHLY threshold = 45 days
            status = v._determine_status(
                coverage=99.0, stale_days=50, frequency=Frequency.MONTHLY
            )
            assert status == HealthStatus.STALE

    def test_ok_monthly_within_threshold(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            status = v._determine_status(
                coverage=99.0, stale_days=30, frequency=Frequency.MONTHLY
            )
            assert status == HealthStatus.OK

    def test_stale_quarterly_threshold(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            # QUARTERLY threshold = 95 days
            status = v._determine_status(
                coverage=99.0, stale_days=100, frequency=Frequency.QUARTERLY
            )
            assert status == HealthStatus.STALE

    def test_gaps_takes_priority_over_stale(self, data_dir: Path) -> None:
        """Coverage baixa retorna GAPS mesmo se tambem stale."""
        with DataValidator(data_dir) as v:
            status = v._determine_status(
                coverage=50.0, stale_days=100, frequency=Frequency.DAILY
            )
            assert status == HealthStatus.GAPS

    def test_boundary_coverage_exactly_95(self, data_dir: Path) -> None:
        """Coverage exatamente no threshold (95.0) -> OK (nao e < 95)."""
        with DataValidator(data_dir) as v:
            status = v._determine_status(
                coverage=95.0, stale_days=0, frequency=Frequency.DAILY
            )
            assert status == HealthStatus.OK

    def test_boundary_coverage_just_below(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            status = v._determine_status(
                coverage=94.99, stale_days=0, frequency=Frequency.DAILY
            )
            assert status == HealthStatus.GAPS


# =========================================================================
# _generate_expected_dates
# =========================================================================


class TestGenerateExpectedDates:
    """Geracao de datas esperadas por frequencia."""

    def test_daily_generates_weekdays(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            # Forcar fallback (sem ANBIMA)
            v._calendar = None
            dates = v._generate_expected_dates(
                date(2024, 1, 2), date(2024, 1, 12), Frequency.DAILY
            )
            # 2024-01-02 (ter) a 2024-01-12 (sex) = 9 business days
            # (2,3,4,5 | 8,9,10,11,12) = 9
            assert len(dates) == 9
            # Sem fins de semana
            for d in dates:
                assert d.weekday() < 5

    def test_monthly_first_of_month(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            dates = v._generate_expected_dates(
                date(2024, 1, 15), date(2024, 6, 30), Frequency.MONTHLY
            )
            # Start ajustado para 2024-01-01, ate 2024-06-30 -> jan,fev,mar,abr,mai,jun = 6
            assert len(dates) == 6
            for d in dates:
                assert d.day == 1

    def test_quarterly(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            dates = v._generate_expected_dates(
                date(2024, 1, 1), date(2024, 12, 31), Frequency.QUARTERLY
            )
            # Q1(jan), Q2(abr), Q3(jul), Q4(out) = 4
            assert len(dates) == 4
            for d in dates:
                assert d.month in (1, 4, 7, 10)

    def test_quarterly_start_mid_quarter(self, data_dir: Path) -> None:
        """Start em fevereiro ajusta para abril (proximo inicio de trimestre)."""
        with DataValidator(data_dir) as v:
            dates = v._generate_expected_dates(
                date(2024, 2, 15), date(2024, 12, 31), Frequency.QUARTERLY
            )
            # Ajusta para abr, jul, out = 3
            assert len(dates) == 3

    def test_empty_range(self, data_dir: Path) -> None:
        """Quando start > end, retorna vazio."""
        with DataValidator(data_dir) as v:
            dates = v._generate_expected_dates(
                date(2024, 6, 1), date(2024, 1, 1), Frequency.DAILY
            )
            # start > end -> deveria ser vazio
            assert len(dates) == 0


# =========================================================================
# _dates_to_gaps
# =========================================================================


class TestDatesToGaps:
    """Agrupamento de datas faltantes em gaps contiguos."""

    def test_empty_missing(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            gaps = v._dates_to_gaps([], Frequency.DAILY)
            assert gaps == []

    def test_single_missing_date(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            v._calendar = None  # fallback weekdays
            gaps = v._dates_to_gaps([date(2024, 1, 3)], Frequency.DAILY)
            assert len(gaps) == 1
            assert gaps[0].expected_records == 1

    def test_contiguous_daily_gap(self, data_dir: Path) -> None:
        """Datas consecutivas formam um unico gap."""
        with DataValidator(data_dir) as v:
            v._calendar = None
            missing = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
            gaps = v._dates_to_gaps(missing, Frequency.DAILY)
            assert len(gaps) == 1
            assert gaps[0].expected_records == 3
            assert gaps[0].start == date(2024, 1, 2)
            assert gaps[0].end == date(2024, 1, 4)

    def test_non_contiguous_creates_multiple_gaps(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            v._calendar = None
            missing = [
                date(2024, 1, 2),
                date(2024, 1, 3),
                # gap break (>5 days)
                date(2024, 2, 1),
                date(2024, 2, 2),
            ]
            gaps = v._dates_to_gaps(missing, Frequency.DAILY)
            assert len(gaps) == 2

    def test_monthly_contiguous(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            missing = [date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)]
            gaps = v._dates_to_gaps(missing, Frequency.MONTHLY)
            assert len(gaps) == 1
            assert gaps[0].expected_records == 3

    def test_monthly_non_contiguous(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            missing = [date(2024, 1, 1), date(2024, 5, 1)]
            gaps = v._dates_to_gaps(missing, Frequency.MONTHLY)
            assert len(gaps) == 2


# =========================================================================
# _is_contiguous
# =========================================================================


class TestIsContiguous:
    """Logica de contiguidade por frequencia."""

    def test_daily_consecutive_weekdays(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            v._calendar = None
            # Seg -> Ter (1 dia)
            assert v._is_contiguous(date(2024, 1, 8), date(2024, 1, 9), Frequency.DAILY)

    def test_daily_friday_to_monday(self, data_dir: Path) -> None:
        """Sex -> Seg (3 dias) deve ser contiguo (fallback <= 5)."""
        with DataValidator(data_dir) as v:
            v._calendar = None
            assert v._is_contiguous(date(2024, 1, 5), date(2024, 1, 8), Frequency.DAILY)

    def test_daily_not_contiguous_far_apart(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            v._calendar = None
            assert not v._is_contiguous(
                date(2024, 1, 2), date(2024, 1, 15), Frequency.DAILY
            )

    def test_monthly_contiguous(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            assert v._is_contiguous(
                date(2024, 1, 1), date(2024, 2, 1), Frequency.MONTHLY
            )

    def test_monthly_december_to_january(self, data_dir: Path) -> None:
        """Dez -> Jan cruza ano."""
        with DataValidator(data_dir) as v:
            assert v._is_contiguous(
                date(2024, 12, 1), date(2025, 1, 1), Frequency.MONTHLY
            )

    def test_monthly_not_contiguous(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            assert not v._is_contiguous(
                date(2024, 1, 1), date(2024, 3, 1), Frequency.MONTHLY
            )

    def test_quarterly_contiguous(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            assert v._is_contiguous(
                date(2024, 1, 1), date(2024, 4, 1), Frequency.QUARTERLY
            )

    def test_quarterly_q4_to_q1(self, data_dir: Path) -> None:
        """Q4 -> Q1 cruza ano."""
        with DataValidator(data_dir) as v:
            assert v._is_contiguous(
                date(2024, 10, 1), date(2025, 1, 1), Frequency.QUARTERLY
            )


# =========================================================================
# get_health (integracao)
# =========================================================================


class TestGetHealth:
    """DataValidator.get_health() integracao completa."""

    def test_missing_file(self, data_dir: Path) -> None:
        with DataValidator(data_dir) as v:
            report = v.get_health("fantasma", "daily", "daily")
            assert report.status == HealthStatus.MISSING

    def test_healthy_recent_data(self, data_dir: Path) -> None:
        """Dados recentes com boa cobertura -> OK."""
        today = date.today()
        # Gerar ultimos 20 business days
        dates = pd.bdate_range(end=today, periods=20)
        df = pd.DataFrame({"date": dates, "value": range(20)})
        filepath = data_dir / "daily" / "selic.parquet"
        _save_parquet(df, filepath)

        with DataValidator(data_dir) as v:
            v._calendar = None  # fallback weekdays
            report = v.get_health("selic", "daily", "daily")
            assert report.status in (HealthStatus.OK, HealthStatus.STALE)
            assert report.actual_records == 20
            assert report.first_date is not None
            assert report.last_date is not None

    def test_file_without_date_column(self, data_dir: Path) -> None:
        """Arquivo sem coluna date retorna OK com coverage 100%."""
        df = pd.DataFrame({"ticker": ["PETR4", "VALE3"], "price": [30.0, 70.0]})
        filepath = data_dir / "daily" / "tickers.parquet"
        _save_parquet(df, filepath)

        with DataValidator(data_dir) as v:
            report = v.get_health("tickers", "daily", "daily")
            assert report.status == HealthStatus.OK
            assert report.coverage == 100.0
            assert report.actual_records == 2

    def test_frequency_string_accepted(self, data_dir: Path) -> None:
        """frequency como string 'monthly' e convertido para Frequency enum."""
        dates = pd.date_range("2024-01-01", periods=6, freq="MS")
        df = pd.DataFrame({"date": dates, "value": range(6)})
        filepath = data_dir / "monthly" / "ipca.parquet"
        _save_parquet(df, filepath)

        with DataValidator(data_dir) as v:
            report = v.get_health("ipca", "monthly", "monthly")
            assert report.actual_records == 6

    def test_context_manager_closes_connection(self, data_dir: Path) -> None:
        v = DataValidator(data_dir)
        v.close()
        assert v._conn is None


# =========================================================================
# HealthReport / HealthStatus (dataclasses)
# =========================================================================


class TestHealthReport:
    """HealthReport e HealthStatus possuem valores esperados."""

    def test_health_status_values(self) -> None:
        assert HealthStatus.OK.value == "ok"
        assert HealthStatus.STALE.value == "stale"
        assert HealthStatus.GAPS.value == "gaps"
        assert HealthStatus.MISSING.value == "missing"

    def test_health_report_defaults(self) -> None:
        report = HealthReport(status=HealthStatus.MISSING)
        assert report.first_date is None
        assert report.last_date is None
        assert report.expected_records == 0
        assert report.actual_records == 0
        assert report.coverage == 0.0
        assert report.gaps == []
        assert report.stale_days == 0

    def test_gap_dataclass(self) -> None:
        gap = Gap(start=date(2024, 1, 1), end=date(2024, 1, 5), expected_records=3)
        assert gap.start == date(2024, 1, 1)
        assert gap.end == date(2024, 1, 5)
        assert gap.expected_records == 3
