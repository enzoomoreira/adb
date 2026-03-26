"""Testes para adb.utils (parse_date, normalize_index)."""

import pandas as pd

from adb.utils import DATE_COLUMNS, normalize_index, parse_date


# =========================================================================
# parse_date
# =========================================================================


class TestParseDate:
    """parse_date normaliza strings de data parciais para YYYY-MM-DD."""

    # --- Adversarial / boundary cases ---

    def test_year_only(self) -> None:
        assert parse_date("2020") == "2020-01-01"

    def test_year_month(self) -> None:
        assert parse_date("2020-06") == "2020-06-01"

    def test_full_date_passthrough(self) -> None:
        assert parse_date("2020-06-15") == "2020-06-15"

    def test_year_with_leading_zeros_not_a_year(self) -> None:
        """Strings de 4 chars sao tratadas como ano -- '0001' e valido."""
        assert parse_date("0001") == "0001-01-01"

    def test_future_year(self) -> None:
        assert parse_date("2099") == "2099-01-01"

    def test_month_boundary_december(self) -> None:
        assert parse_date("2020-12") == "2020-12-01"

    def test_month_boundary_january(self) -> None:
        assert parse_date("2020-01") == "2020-01-01"

    def test_full_date_end_of_month(self) -> None:
        """Datas como 31 de janeiro passam direto sem validacao."""
        assert parse_date("2020-01-31") == "2020-01-31"

    def test_invalid_month_passes_through(self) -> None:
        """parse_date nao valida meses -- '2020-13' retorna '2020-13-01'.
        Isso e intencional: a validacao de data valida fica a cargo do caller.
        """
        result = parse_date("2020-13")
        assert result == "2020-13-01"

    def test_longer_string_passthrough(self) -> None:
        """Strings com len > 10 (ex: ISO com timezone) passam direto."""
        iso = "2020-06-15T10:30:00"
        assert parse_date(iso) == iso

    def test_empty_string_passthrough(self) -> None:
        """String vazia passa direto (len != 4 e len != 7)."""
        assert parse_date("") == ""

    def test_three_char_string_passthrough(self) -> None:
        """Strings de 3 chars nao sao tratadas como ano."""
        assert parse_date("abc") == "abc"


# =========================================================================
# normalize_index
# =========================================================================


class TestNormalizeIndex:
    """normalize_index padroniza DataFrames para DatetimeIndex com nome 'date'."""

    # --- Caso 1: DataFrame ja com DatetimeIndex ---

    def test_datetime_index_preserves_data(
        self, ts_with_datetime_index: pd.DataFrame
    ) -> None:
        result = normalize_index(ts_with_datetime_index)
        assert result.index.name == "date"
        assert pd.api.types.is_datetime64_any_dtype(result.index)
        assert len(result) == 5

    def test_datetime_index_normalizes_time_component(self) -> None:
        """Timestamps com hora devem ser normalizados para meia-noite."""
        idx = pd.DatetimeIndex(
            ["2024-01-02 14:30:00", "2024-01-03 09:15:00"], name="foo"
        )
        df = pd.DataFrame({"value": [1, 2]}, index=idx)
        result = normalize_index(df)
        assert result.index.name == "date"
        assert all(t.hour == 0 for t in result.index)

    def test_datetime_index_renames_existing_name(self) -> None:
        """Indices com outro nome (ex: 'timestamp') sao renomeados."""
        idx = pd.DatetimeIndex(
            pd.bdate_range("2024-01-02", periods=3), name="timestamp"
        )
        df = pd.DataFrame({"value": [1, 2, 3]}, index=idx)
        result = normalize_index(df)
        assert result.index.name == "date"

    # --- Caso 2: DataFrame com coluna de data ---

    def test_date_column_moved_to_index(self, ts_daily: pd.DataFrame) -> None:
        result = normalize_index(ts_daily)
        assert result.index.name == "date"
        assert "date" not in result.columns
        assert pd.api.types.is_datetime64_any_dtype(result.index)

    def test_variant_column_data(self, ts_variant_column: pd.DataFrame) -> None:
        """Coluna 'Data' (portugues) e reconhecida e movida para indice."""
        result = normalize_index(ts_variant_column)
        assert result.index.name == "date"
        assert "Data" not in result.columns

    def test_date_column_priority_order(self) -> None:
        """Se existem 'date' E 'Data', 'date' tem prioridade (primeiro em DATE_COLUMNS)."""
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=2),
                "Data": pd.date_range("2025-01-01", periods=2),
                "value": [1, 2],
            }
        )
        result = normalize_index(df)
        assert result.index.name == "date"
        # Deve usar 'date', nao 'Data'
        assert result.index[0].year == 2024

    def test_string_date_column_converted(self) -> None:
        """Colunas de data como string sao convertidas para datetime."""
        df = pd.DataFrame({"date": ["2024-01-01", "2024-02-01"], "value": [10, 20]})
        result = normalize_index(df)
        assert pd.api.types.is_datetime64_any_dtype(result.index)

    # --- Caso 3: Sem coluna de data ---

    def test_no_date_column_returns_unchanged(self) -> None:
        df = pd.DataFrame({"ticker": ["PETR4", "VALE3"], "price": [30.0, 70.0]})
        result = normalize_index(df)
        # Deve retornar inalterado
        assert list(result.columns) == ["ticker", "price"]
        assert not pd.api.types.is_datetime64_any_dtype(result.index)

    # --- Edge cases ---

    def test_empty_dataframe(self) -> None:
        df = pd.DataFrame()
        result = normalize_index(df)
        assert result.empty

    def test_single_row(self) -> None:
        df = pd.DataFrame({"date": [pd.Timestamp("2024-06-15")], "value": [42]})
        result = normalize_index(df)
        assert result.index.name == "date"
        assert len(result) == 1


class TestDateColumns:
    """Verifica que DATE_COLUMNS cobre variantes esperadas."""

    def test_contains_expected_variants(self) -> None:
        expected = {"date", "Date", "data", "Data", "DATE"}
        assert set(DATE_COLUMNS) == expected

    def test_lowercase_date_first(self) -> None:
        """'date' deve ser o primeiro item (prioridade maxima)."""
        assert DATE_COLUMNS[0] == "date"
