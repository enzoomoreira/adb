"""Testes para adb.infra.query (QueryEngine)."""

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from adb.infra.query import QueryEngine


def _save_parquet(df: pd.DataFrame, filepath: Path) -> None:
    """Helper para salvar DataFrame como Parquet via DuckDB."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    duckdb.register("_test_df", df)
    try:
        duckdb.sql(
            f"COPY _test_df TO '{filepath}' (FORMAT 'parquet', COMPRESSION 'snappy')"
        )
    finally:
        duckdb.unregister("_test_df")


@pytest.fixture
def qe(data_dir: Path) -> QueryEngine:
    return QueryEngine(base_path=data_dir, progress_bar=False)


@pytest.fixture
def saved_daily(data_dir: Path) -> Path:
    """Cria selic.parquet com 10 registros diarios."""
    dates = pd.bdate_range("2024-01-02", periods=10)
    df = pd.DataFrame({"date": dates, "value": range(100, 110)})
    filepath = data_dir / "daily" / "selic.parquet"
    _save_parquet(df, filepath)
    return filepath


@pytest.fixture
def saved_multicolumn(data_dir: Path) -> Path:
    """Cria arquivo com multiplas colunas para testar agregacao."""
    dates = pd.bdate_range("2024-01-02", periods=6)
    df = pd.DataFrame(
        {
            "date": dates,
            "uf": [35, 35, 33, 33, 31, 31],
            "value": [100, 200, 150, 250, 120, 220],
        }
    )
    filepath = data_dir / "monthly" / "emprego.parquet"
    _save_parquet(df, filepath)
    return filepath


# =========================================================================
# _query (construcao SQL)
# =========================================================================


class TestQueryBuilder:
    """QueryEngine._query() constroi SQL correto."""

    def test_select_all(self, qe: QueryEngine, saved_daily: Path) -> None:
        sql = qe._query(str(saved_daily))
        assert "SELECT *" in sql
        assert str(saved_daily) in sql

    def test_select_columns_includes_date(
        self, qe: QueryEngine, saved_daily: Path
    ) -> None:
        """Colunas especificas devem incluir 'date' automaticamente."""
        sql = qe._query(str(saved_daily), columns=["value"])
        assert "date" in sql
        assert "value" in sql

    def test_select_columns_with_date_already(
        self, qe: QueryEngine, saved_daily: Path
    ) -> None:
        """Se 'date' ja esta nas colunas, nao duplica."""
        sql = qe._query(str(saved_daily), columns=["date", "value"])
        # Conta ocorrencias de 'date' no SELECT
        select_part = sql.split("FROM")[0]
        assert select_part.count("date") == 1

    def test_where_clause(self, qe: QueryEngine, saved_daily: Path) -> None:
        sql = qe._query(str(saved_daily), where="date >= '2024-01-05'")
        assert "WHERE date >= '2024-01-05'" in sql

    def test_no_where(self, qe: QueryEngine, saved_daily: Path) -> None:
        sql = qe._query(str(saved_daily))
        assert "WHERE" not in sql


# =========================================================================
# read
# =========================================================================


class TestRead:
    """QueryEngine.read() le arquivos Parquet."""

    def test_read_all(self, qe: QueryEngine, saved_daily: Path) -> None:
        df = qe.read("selic", "daily")
        assert len(df) == 10

    def test_read_with_where(self, qe: QueryEngine, saved_daily: Path) -> None:
        df = qe.read("selic", "daily", where="date >= '2024-01-08'")
        assert len(df) < 10
        assert len(df) > 0

    def test_read_specific_columns(self, qe: QueryEngine, saved_daily: Path) -> None:
        df = qe.read("selic", "daily", columns=["value"])
        assert "value" in df.columns
        # date tambem incluido via _ensure_dates
        assert "date" in df.columns

    def test_read_nonexistent_returns_empty(self, qe: QueryEngine) -> None:
        df = qe.read("fantasma", "daily")
        assert df.empty


# =========================================================================
# read_glob
# =========================================================================


class TestReadGlob:
    """QueryEngine.read_glob() le multiplos arquivos."""

    def test_read_glob_single_match(self, qe: QueryEngine, saved_daily: Path) -> None:
        df = qe.read_glob("selic.parquet", subdir="daily")
        assert len(df) == 10

    def test_read_glob_wildcard(self, qe: QueryEngine, data_dir: Path) -> None:
        """*.parquet captura todos os arquivos do subdir."""
        dates = pd.bdate_range("2024-01-02", periods=5)
        for name in ["selic", "cdi"]:
            df = pd.DataFrame({"date": dates, "value": range(5)})
            _save_parquet(df, data_dir / "daily" / f"{name}.parquet")

        result = qe.read_glob("*.parquet", subdir="daily")
        assert len(result) == 10

    def test_read_glob_no_match_returns_empty(self, qe: QueryEngine) -> None:
        df = qe.read_glob("*.parquet", subdir="nonexistent")
        assert df.empty


# =========================================================================
# aggregate
# =========================================================================


class TestAggregate:
    """QueryEngine.aggregate() executa agregacoes SQL."""

    def test_aggregate_avg(self, qe: QueryEngine, saved_multicolumn: Path) -> None:
        result = qe.aggregate("emprego", "monthly", group_by="uf", agg={"value": "AVG"})
        assert len(result) == 3  # 3 UFs: 35, 33, 31
        assert "value" in result.columns
        assert "uf" in result.columns

    def test_aggregate_with_where(
        self, qe: QueryEngine, saved_multicolumn: Path
    ) -> None:
        result = qe.aggregate(
            "emprego",
            "monthly",
            group_by="uf",
            agg={"value": "SUM"},
            where="uf = 35",
        )
        assert len(result) == 1
        assert result.iloc[0]["uf"] == 35

    def test_aggregate_multiple_group_cols(
        self, qe: QueryEngine, saved_multicolumn: Path
    ) -> None:
        result = qe.aggregate(
            "emprego",
            "monthly",
            group_by=["uf"],
            agg={"value": "COUNT(*)"},
        )
        assert len(result) == 3


# =========================================================================
# get_metadata
# =========================================================================


class TestGetMetadata:
    """QueryEngine.get_metadata() retorna info do arquivo."""

    def test_metadata_basic(self, qe: QueryEngine, saved_daily: Path) -> None:
        meta = qe.get_metadata("selic", "daily")
        assert meta is not None
        assert meta["registros"] == 10
        assert meta["status"] == "OK"
        assert meta["primeira_data"] is not None
        assert meta["ultima_data"] is not None

    def test_metadata_nonexistent(self, qe: QueryEngine) -> None:
        meta = qe.get_metadata("fantasma", "daily")
        assert meta is None

    def test_metadata_dates_are_timestamps(
        self, qe: QueryEngine, saved_daily: Path
    ) -> None:
        meta = qe.get_metadata("selic", "daily")
        assert meta is not None
        assert isinstance(meta["primeira_data"], pd.Timestamp)
        assert isinstance(meta["ultima_data"], pd.Timestamp)


# =========================================================================
# sql (raw)
# =========================================================================


class TestRawSql:
    """QueryEngine.sql() executa SQL arbitrario."""

    def test_sql_with_base_substitution(
        self, qe: QueryEngine, saved_daily: Path
    ) -> None:
        result = qe.sql("SELECT COUNT(*) as cnt FROM '{base}/daily/selic.parquet'")
        assert result.iloc[0]["cnt"] == 10

    def test_sql_with_subdir_substitution(
        self, qe: QueryEngine, saved_daily: Path
    ) -> None:
        result = qe.sql(
            "SELECT COUNT(*) as cnt FROM '{subdir}/selic.parquet'",
            subdir="daily",
        )
        assert result.iloc[0]["cnt"] == 10
