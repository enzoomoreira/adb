"""Testes para adb.collector (BaseCollector)."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from .conftest import FAKE_CONFIG


def _make_collector(**overrides) -> "BaseCollector":
    """Cria BaseCollector com mocks para display."""
    from adb.collector import BaseCollector

    defaults = {
        "config": FAKE_CONFIG,
        "title": "Test Collector",
        "client_class": MagicMock,
        "subdir_template": "test/{frequency}",
        "data_path": overrides.pop("data_path", "/tmp/fake"),
    }
    defaults.update(overrides)
    return BaseCollector(**defaults)


@pytest.fixture(autouse=True)
def _mock_display():
    """Mock get_display para todos os testes do collector."""
    with patch("adb.display.get_display", return_value=MagicMock()):
        yield


# =========================================================================
# _normalize_indicators
# =========================================================================


class TestNormalizeIndicators:
    """_normalize_indicators converte input para lista de keys."""

    def test_all_string(self) -> None:
        c = _make_collector()
        result = c._normalize_indicators("all")
        assert result == list(FAKE_CONFIG.keys())

    def test_single_string(self) -> None:
        c = _make_collector()
        result = c._normalize_indicators("selic")
        assert result == ["selic"]

    def test_list_passthrough(self) -> None:
        c = _make_collector()
        result = c._normalize_indicators(["selic", "ipca"])
        assert result == ["selic", "ipca"]

    def test_empty_list(self) -> None:
        c = _make_collector()
        result = c._normalize_indicators([])
        assert result == []

    def test_tuple_converted_to_list(self) -> None:
        c = _make_collector()
        result = c._normalize_indicators(("selic", "pib"))
        assert result == ["selic", "pib"]


# =========================================================================
# _resolve_subdir
# =========================================================================


class TestResolveSubdir:
    """_resolve_subdir interpola template com frequency do config."""

    def test_daily_frequency(self) -> None:
        c = _make_collector()
        subdir = c._resolve_subdir(FAKE_CONFIG["selic"])
        assert subdir == "test/daily"

    def test_monthly_frequency(self) -> None:
        c = _make_collector()
        subdir = c._resolve_subdir(FAKE_CONFIG["ipca"])
        assert subdir == "test/monthly"

    def test_quarterly_frequency(self) -> None:
        c = _make_collector()
        subdir = c._resolve_subdir(FAKE_CONFIG["pib"])
        assert subdir == "test/quarterly"

    def test_no_frequency_placeholder(self) -> None:
        """Template sem {frequency} retorna literal."""
        c = _make_collector(subdir_template="bacen/sgs")
        subdir = c._resolve_subdir(FAKE_CONFIG["selic"])
        assert subdir == "bacen/sgs"

    def test_missing_frequency_defaults_daily(self) -> None:
        """Config sem 'frequency' usa 'daily' como default."""
        c = _make_collector()
        config_no_freq = {"code": 999, "name": "Teste"}
        subdir = c._resolve_subdir(config_no_freq)
        assert subdir == "test/daily"


# =========================================================================
# _next_date
# =========================================================================


class TestNextDate:
    """_next_date calcula proxima data baseado na frequencia."""

    def test_daily_next_day(self) -> None:
        c = _make_collector()
        result = c._next_date(pd.Timestamp("2024-01-15"), "daily")
        assert result == "2024-01-16"

    def test_monthly_next_month(self) -> None:
        c = _make_collector()
        result = c._next_date(pd.Timestamp("2024-01-15"), "monthly")
        assert result == "2024-02-01"

    def test_monthly_december_wraps_year(self) -> None:
        c = _make_collector()
        result = c._next_date(pd.Timestamp("2024-12-01"), "monthly")
        assert result == "2025-01-01"

    def test_quarterly_q1_to_q2(self) -> None:
        c = _make_collector()
        result = c._next_date(pd.Timestamp("2024-03-15"), "quarterly")
        assert result == "2024-04-01"

    def test_quarterly_q4_wraps_year(self) -> None:
        c = _make_collector()
        result = c._next_date(pd.Timestamp("2024-10-01"), "quarterly")
        assert result == "2025-01-01"

    def test_quarterly_q3_to_q4(self) -> None:
        c = _make_collector()
        result = c._next_date(pd.Timestamp("2024-07-01"), "quarterly")
        assert result == "2024-10-01"

    def test_none_returns_none(self) -> None:
        c = _make_collector()
        result = c._next_date(None, "daily")
        assert result is None

    def test_nat_returns_none(self) -> None:
        c = _make_collector()
        result = c._next_date(pd.NaT, "daily")
        assert result is None

    def test_monthly_end_of_month_31(self) -> None:
        """Janeiro 31 -> calcula proximo mes.
        Logica: replace(day=1) = jan 1, + 32 dias = fev 2, replace(day=1) = fev 1.
        """
        c = _make_collector()
        result = c._next_date(pd.Timestamp("2024-01-31"), "monthly")
        assert result == "2024-02-01"

    def test_monthly_mid_month(self) -> None:
        """Qualquer dia do mes -> primeiro dia do proximo mes."""
        c = _make_collector()
        result = c._next_date(pd.Timestamp("2024-03-15"), "monthly")
        assert result == "2024-04-01"


# =========================================================================
# _get_frequency_for_file
# =========================================================================


class TestGetFrequencyForFile:
    """_get_frequency_for_file retorna frequency do config."""

    def test_known_indicator(self) -> None:
        c = _make_collector()
        assert c._get_frequency_for_file("selic") == "daily"
        assert c._get_frequency_for_file("ipca") == "monthly"
        assert c._get_frequency_for_file("pib") == "quarterly"

    def test_unknown_indicator(self) -> None:
        c = _make_collector()
        assert c._get_frequency_for_file("desconhecido") is None
