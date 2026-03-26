"""Testes para adb.explorer (BaseExplorer)."""

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from adb.explorer import BaseExplorer

from .conftest import FAKE_CONFIG


class FakeExplorer(BaseExplorer):
    """Explorer concreto para testes com config fake."""

    _CONFIG = FAKE_CONFIG
    _SUBDIR_TEMPLATE = "test/{frequency}"
    _CLIENT_CLASS = MagicMock
    _TITLE = "Fake Explorer"


@pytest.fixture
def explorer(data_dir: Path) -> FakeExplorer:
    """Cria FakeExplorer com QueryEngine apontando para tmp_path."""
    from adb.infra.query import QueryEngine

    qe = QueryEngine(base_path=data_dir, progress_bar=False)
    return FakeExplorer(query_engine=qe)


# =========================================================================
# _subdir
# =========================================================================


class TestSubdir:
    """_subdir resolve template com frequency do config."""

    def test_daily(self, explorer: FakeExplorer) -> None:
        assert explorer._subdir("selic") == "test/daily"

    def test_monthly(self, explorer: FakeExplorer) -> None:
        assert explorer._subdir("ipca") == "test/monthly"

    def test_quarterly(self, explorer: FakeExplorer) -> None:
        assert explorer._subdir("pib") == "test/quarterly"


# =========================================================================
# _where
# =========================================================================


class TestWhere:
    """_where constroi clausula WHERE SQL."""

    def test_no_filters(self, explorer: FakeExplorer) -> None:
        assert explorer._where() is None

    def test_start_only(self, explorer: FakeExplorer) -> None:
        result = explorer._where(start="2020")
        assert result == "date >= '2020-01-01'"

    def test_end_only(self, explorer: FakeExplorer) -> None:
        result = explorer._where(end="2024-06")
        assert result == "date <= '2024-06-01'"

    def test_start_and_end(self, explorer: FakeExplorer) -> None:
        result = explorer._where(start="2020", end="2024")
        assert "date >= '2020-01-01'" in result
        assert "date <= '2024-01-01'" in result
        assert " AND " in result

    def test_full_date_format(self, explorer: FakeExplorer) -> None:
        result = explorer._where(start="2020-03-15")
        assert result == "date >= '2020-03-15'"


# =========================================================================
# available
# =========================================================================


class TestAvailable:
    """available() lista e filtra indicadores."""

    def test_all_indicators(self, explorer: FakeExplorer) -> None:
        result = explorer.available()
        assert set(result) == {"selic", "ipca", "pib"}

    def test_filter_by_frequency(self, explorer: FakeExplorer) -> None:
        result = explorer.available(frequency="daily")
        assert result == ["selic"]

    def test_filter_no_match(self, explorer: FakeExplorer) -> None:
        result = explorer.available(frequency="yearly")
        assert result == []

    def test_filter_by_multiple_attrs(self, explorer: FakeExplorer) -> None:
        result = explorer.available(frequency="daily", code=11)
        assert result == ["selic"]

    def test_filter_partial_match_excluded(self, explorer: FakeExplorer) -> None:
        """Filtro deve casar TODOS os atributos."""
        result = explorer.available(frequency="daily", code=999)
        assert result == []


# =========================================================================
# info
# =========================================================================


class TestInfo:
    """info() retorna configuracao de indicadores."""

    def test_single_indicator(self, explorer: FakeExplorer) -> None:
        result = explorer.info("selic")
        assert result["code"] == 11
        assert result["name"] == "Taxa Selic"

    def test_returns_copy(self, explorer: FakeExplorer) -> None:
        """Deve retornar copia, nao referencia ao config original."""
        result = explorer.info("selic")
        result["code"] = 9999
        assert FAKE_CONFIG["selic"]["code"] == 11

    def test_all_indicators(self, explorer: FakeExplorer) -> None:
        result = explorer.info()
        assert len(result) == 3

    def test_unknown_indicator_raises(self, explorer: FakeExplorer) -> None:
        with pytest.raises(KeyError, match="nao encontrado"):
            explorer.info("desconhecido")


# =========================================================================
# read (com QueryEngine real)
# =========================================================================


class TestRead:
    """BaseExplorer.read() le dados do disco."""

    def _save_indicator(
        self, data_dir: Path, name: str, subdir: str, n: int = 5
    ) -> None:
        """Salva indicador fake como Parquet."""
        import duckdb

        dates = pd.bdate_range("2024-01-02", periods=n)
        df = pd.DataFrame({"date": dates, "value": range(n)})
        filepath = data_dir / subdir / f"{name}.parquet"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        duckdb.register("_test_df", df)
        try:
            duckdb.sql(
                f"COPY _test_df TO '{filepath}' (FORMAT 'parquet', COMPRESSION 'snappy')"
            )
        finally:
            duckdb.unregister("_test_df")

    def test_read_single_indicator(
        self, explorer: FakeExplorer, data_dir: Path
    ) -> None:
        self._save_indicator(data_dir, "selic", "test/daily")
        df = explorer.read("selic")
        assert not df.empty
        assert "selic" in df.columns  # coluna 'value' renomeada

    def test_read_multiple_indicators_joins(
        self, explorer: FakeExplorer, data_dir: Path
    ) -> None:
        self._save_indicator(data_dir, "selic", "test/daily")
        self._save_indicator(data_dir, "ipca", "test/monthly", n=3)
        df = explorer.read("selic", "ipca")
        assert "selic" in df.columns
        assert "ipca" in df.columns

    def test_read_unknown_indicator_raises(self, explorer: FakeExplorer) -> None:
        with pytest.raises(KeyError, match="nao encontrado"):
            explorer.read("desconhecido")

    def test_read_nonexistent_data_returns_empty(self, explorer: FakeExplorer) -> None:
        """Indicador valido mas sem dados no disco -> DataFrame vazio."""
        df = explorer.read("selic")
        assert df.empty

    def test_read_with_date_filter(
        self, explorer: FakeExplorer, data_dir: Path
    ) -> None:
        self._save_indicator(data_dir, "selic", "test/daily", n=20)
        df = explorer.read("selic", start="2024-01-10")
        assert not df.empty
        assert df.index.min() >= pd.Timestamp("2024-01-10")

    def test_read_all_defaults_to_all_indicators(
        self, explorer: FakeExplorer, data_dir: Path
    ) -> None:
        """read() sem argumentos tenta ler todos os indicadores configurados."""
        self._save_indicator(data_dir, "selic", "test/daily")
        self._save_indicator(data_dir, "ipca", "test/monthly")
        self._save_indicator(data_dir, "pib", "test/quarterly")
        df = explorer.read()
        # Deve ter colunas para cada indicador com dados
        assert len(df.columns) >= 1


# =========================================================================
# _join
# =========================================================================


class TestJoin:
    """_join concatena DataFrames por indice."""

    def test_empty_list(self, explorer: FakeExplorer) -> None:
        result = explorer._join([], ())
        assert result.empty

    def test_single_df(self, explorer: FakeExplorer) -> None:
        idx = pd.DatetimeIndex(pd.bdate_range("2024-01-02", periods=3), name="date")
        df = pd.DataFrame({"selic": [1, 2, 3]}, index=idx)
        result = explorer._join([df], ("selic",))
        assert len(result) == 3

    def test_multiple_dfs_outer_join(self, explorer: FakeExplorer) -> None:
        """DataFrames com indices diferentes fazem outer join."""
        idx1 = pd.DatetimeIndex(["2024-01-02", "2024-01-03", "2024-01-04"], name="date")
        idx2 = pd.DatetimeIndex(["2024-01-03", "2024-01-04", "2024-01-05"], name="date")
        df1 = pd.DataFrame({"selic": [1, 2, 3]}, index=idx1)
        df2 = pd.DataFrame({"cdi": [10, 20, 30]}, index=idx2)
        result = explorer._join([df1, df2], ("selic", "cdi"))
        # Outer join: 2,3,4,5 = 4 datas
        assert len(result) == 4
        assert "selic" in result.columns
        assert "cdi" in result.columns


# =========================================================================
# __init__.py (lazy loading)
# =========================================================================


class TestLazyRegistry:
    """adb.__getattr__ e available_sources."""

    def test_available_sources(self) -> None:
        import adb

        sources = adb.available_sources()
        assert "sgs" in sources
        assert "expectations" in sources
        assert "ipea" in sources
        assert "sidra" in sources
        assert "bloomberg" in sources

    def test_unknown_attr_raises(self) -> None:
        import adb

        with pytest.raises(AttributeError, match="has no attribute"):
            _ = adb.nonexistent_explorer
