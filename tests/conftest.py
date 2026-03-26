"""Fixtures compartilhadas para a suite de testes."""

from pathlib import Path

import duckdb
import pandas as pd
import pytest


# =========================================================================
# Fixtures de diretorio temporario
# =========================================================================


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Diretorio temporario simulando data_dir do Settings."""
    return tmp_path


@pytest.fixture
def daily_dir(data_dir: Path) -> Path:
    """Subdiretorio daily dentro do data_dir."""
    path = data_dir / "daily"
    path.mkdir()
    return path


# =========================================================================
# DataFrames de exemplo
# =========================================================================


@pytest.fixture
def ts_daily() -> pd.DataFrame:
    """Serie temporal diaria com coluna date + value."""
    dates = pd.bdate_range("2024-01-02", periods=10)
    return pd.DataFrame({"date": dates, "value": range(100, 110)})


@pytest.fixture
def ts_monthly() -> pd.DataFrame:
    """Serie temporal mensal."""
    dates = pd.date_range("2024-01-01", periods=6, freq="MS")
    return pd.DataFrame({"date": dates, "value": [1.1, 2.2, 3.3, 4.4, 5.5, 6.6]})


@pytest.fixture
def ts_with_datetime_index() -> pd.DataFrame:
    """DataFrame ja com DatetimeIndex."""
    idx = pd.DatetimeIndex(pd.bdate_range("2024-01-02", periods=5), name="date")
    return pd.DataFrame({"value": [10, 20, 30, 40, 50]}, index=idx)


@pytest.fixture
def ts_variant_column() -> pd.DataFrame:
    """DataFrame com coluna 'Data' (variante portuguesa)."""
    dates = pd.date_range("2024-01-01", periods=3, freq="MS")
    return pd.DataFrame({"Data": dates, "valor": [1, 2, 3]})


# =========================================================================
# Fixtures de Parquet (pre-salvos para testes de leitura)
# =========================================================================


@pytest.fixture
def parquet_daily(daily_dir: Path, ts_daily: pd.DataFrame) -> Path:
    """Salva ts_daily como Parquet e retorna o path."""
    filepath = daily_dir / "selic.parquet"
    duckdb.register("_fixture_df", ts_daily)
    try:
        duckdb.sql(
            f"COPY _fixture_df TO '{filepath}' (FORMAT 'parquet', COMPRESSION 'snappy')"
        )
    finally:
        duckdb.unregister("_fixture_df")
    return filepath


# =========================================================================
# Config de explorer fake (para testes unitarios)
# =========================================================================


FAKE_CONFIG: dict = {
    "selic": {
        "code": 11,
        "name": "Taxa Selic",
        "frequency": "daily",
        "description": "Taxa basica de juros",
    },
    "ipca": {
        "code": 433,
        "name": "IPCA Mensal",
        "frequency": "monthly",
        "description": "Indice de precos ao consumidor",
    },
    "pib": {
        "code": 22109,
        "name": "PIB Trimestral",
        "frequency": "quarterly",
        "description": "Produto interno bruto",
    },
}
