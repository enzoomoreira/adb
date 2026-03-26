"""Testes para adb.infra.storage (DataManager)."""

from pathlib import Path

import duckdb
import pandas as pd

from adb.infra.storage import DataManager, NullCallback


def _make_manager(data_dir: Path) -> DataManager:
    """Cria DataManager com base_path customizado (sem acessar Settings)."""
    return DataManager(base_path=data_dir, callback=NullCallback())


def _read_parquet(filepath: Path) -> pd.DataFrame:
    """Le Parquet com conexao DuckDB fresca (evita cache do global connection)."""
    conn = duckdb.connect()
    try:
        return conn.execute(f"SELECT * FROM '{filepath}' ORDER BY date").df()
    finally:
        conn.close()


# =========================================================================
# save + read roundtrip
# =========================================================================


class TestSaveRead:
    """DataManager.save() persiste DataFrame e read() recupera."""

    def test_save_creates_parquet(self, data_dir: Path, ts_daily: pd.DataFrame) -> None:
        dm = _make_manager(data_dir)
        dm.save(ts_daily, "selic", subdir="daily")
        assert (data_dir / "daily" / "selic.parquet").exists()

    def test_save_creates_subdir(self, data_dir: Path, ts_daily: pd.DataFrame) -> None:
        """Subdiretorios inexistentes sao criados automaticamente."""
        dm = _make_manager(data_dir)
        dm.save(ts_daily, "selic", subdir="bacen/sgs/daily")
        assert (data_dir / "bacen" / "sgs" / "daily" / "selic.parquet").exists()

    def test_read_returns_saved_data(
        self, data_dir: Path, ts_daily: pd.DataFrame
    ) -> None:
        dm = _make_manager(data_dir)
        dm.save(ts_daily, "selic", subdir="daily")
        result = dm.read("selic", subdir="daily")
        assert not result.empty
        assert len(result) == len(ts_daily)

    def test_read_nonexistent_returns_empty(self, data_dir: Path) -> None:
        dm = _make_manager(data_dir)
        result = dm.read("fantasma", subdir="daily")
        assert result.empty

    def test_save_normalizes_index(
        self, data_dir: Path, ts_daily: pd.DataFrame
    ) -> None:
        """save() chama normalize_index: resultado deve ter coluna 'date'."""
        dm = _make_manager(data_dir)
        dm.save(ts_daily, "selic", subdir="daily")

        filepath = data_dir / "daily" / "selic.parquet"
        conn = duckdb.connect()
        schema = conn.execute(f"DESCRIBE SELECT * FROM '{filepath}' LIMIT 0").df()
        conn.close()
        columns = set(schema["column_name"].values)
        assert "date" in columns
        assert "value" in columns

    def test_save_with_datetime_index(
        self, data_dir: Path, ts_with_datetime_index: pd.DataFrame
    ) -> None:
        """DataFrames ja indexados tambem sao salvos corretamente."""
        dm = _make_manager(data_dir)
        dm.save(ts_with_datetime_index, "indexed", subdir="daily")
        result = dm.read("indexed", subdir="daily")
        assert not result.empty

    def test_save_overwrites_existing(
        self, data_dir: Path, ts_daily: pd.DataFrame
    ) -> None:
        """Salvar no mesmo nome sobrescreve o arquivo anterior."""
        dm = _make_manager(data_dir)
        dm.save(ts_daily, "selic", subdir="daily")

        smaller = ts_daily.head(3)
        dm.save(smaller, "selic", subdir="daily")

        result = dm.read("selic", subdir="daily")
        assert len(result) == 3


# =========================================================================
# append (com dedup)
# =========================================================================


class TestAppend:
    """DataManager.append() adiciona dados incrementalmente."""

    def test_append_to_nonexistent_creates_file(
        self, data_dir: Path, ts_daily: pd.DataFrame
    ) -> None:
        """Append em arquivo inexistente equivale a save."""
        dm = _make_manager(data_dir)
        dm.append(ts_daily, "selic", subdir="daily")
        assert (data_dir / "daily" / "selic.parquet").exists()

    def test_append_adds_new_records(self, data_dir: Path) -> None:
        dm = _make_manager(data_dir)

        # Bloco 1: jan
        df1 = pd.DataFrame(
            {
                "date": pd.bdate_range("2024-01-02", periods=5),
                "value": range(5),
            }
        )
        dm.save(df1, "selic", subdir="daily")

        # Bloco 2: fev (sem overlap)
        df2 = pd.DataFrame(
            {
                "date": pd.bdate_range("2024-02-01", periods=5),
                "value": range(100, 105),
            }
        )
        dm.append(df2, "selic", subdir="daily")

        # Verificar conteudo do arquivo com conexao fresca
        filepath = data_dir / "daily" / "selic.parquet"
        result = _read_parquet(filepath)
        assert len(result) == 10

    def test_append_dedup_keeps_latest(self, data_dir: Path) -> None:
        """Dedup por date: registros novos sobrescrevem antigos."""
        dm = _make_manager(data_dir)

        dates = pd.bdate_range("2024-01-02", periods=3)
        df1 = pd.DataFrame({"date": dates, "value": [1, 2, 3]})
        dm.save(df1, "selic", subdir="daily")

        # Mesmas datas, valores diferentes
        df2 = pd.DataFrame({"date": dates, "value": [10, 20, 30]})
        dm.append(df2, "selic", subdir="daily", dedup=True)

        filepath = data_dir / "daily" / "selic.parquet"
        result = _read_parquet(filepath)
        assert len(result) == 3
        assert list(result["value"]) == [10, 20, 30]

    def test_append_no_dedup_keeps_all(self, data_dir: Path) -> None:
        """dedup=False mantem todos os registros (inclusive duplicatas)."""
        dm = _make_manager(data_dir)

        dates = pd.bdate_range("2024-01-02", periods=3)
        df1 = pd.DataFrame({"date": dates, "value": [1, 2, 3]})
        dm.save(df1, "selic", subdir="daily")

        df2 = pd.DataFrame({"date": dates, "value": [10, 20, 30]})
        dm.append(df2, "selic", subdir="daily", dedup=False)

        filepath = data_dir / "daily" / "selic.parquet"
        result = _read_parquet(filepath)
        assert len(result) == 6

    def test_append_partial_overlap(self, data_dir: Path) -> None:
        """Overlap parcial: datas novas adicionadas, sobrepostas atualizadas."""
        dm = _make_manager(data_dir)

        dates1 = pd.bdate_range("2024-01-02", periods=5)
        df1 = pd.DataFrame({"date": dates1, "value": [1, 2, 3, 4, 5]})
        dm.save(df1, "selic", subdir="daily")

        # Overlap nas ultimas 2 datas + 3 novas
        dates2 = pd.bdate_range("2024-01-08", periods=5)
        df2 = pd.DataFrame({"date": dates2, "value": [40, 50, 60, 70, 80]})
        dm.append(df2, "selic", subdir="daily", dedup=True)

        filepath = data_dir / "daily" / "selic.parquet"
        result = _read_parquet(filepath)
        # dates1: Jan 2,3,4,5,8 | dates2: Jan 8,9,10,11,12 | overlap: Jan 8
        # 5 originais + 5 novas - 1 sobreposta = 9
        assert len(result) == 9

    def test_append_atomic_on_error(self, data_dir: Path) -> None:
        """Se append falha, arquivo original nao e corrompido."""
        dm = _make_manager(data_dir)

        dates = pd.bdate_range("2024-01-02", periods=3)
        df1 = pd.DataFrame({"date": dates, "value": [1, 2, 3]})
        dm.save(df1, "selic", subdir="daily")

        filepath = data_dir / "daily" / "selic.parquet"
        original_size = filepath.stat().st_size

        # DataFrame com tipo incompativel para forcar erro
        bad_df = pd.DataFrame({"date": ["not-a-date"], "value": ["not-a-number"]})
        try:
            dm.append(bad_df, "selic", subdir="daily")
        except Exception:
            pass

        # Arquivo original deve estar intacto
        assert filepath.exists()
        assert filepath.stat().st_size == original_size


# =========================================================================
# read after append (expoe fraqueza do DuckDB global connection)
# =========================================================================


class TestReadAfterAppend:
    """Testa se DataManager.read() funciona apos append no mesmo processo."""

    def test_read_after_append_returns_data(self, data_dir: Path) -> None:
        """dm.read() deve retornar dados apos dm.append()."""
        dm = _make_manager(data_dir)

        df1 = pd.DataFrame(
            {
                "date": pd.bdate_range("2024-01-02", periods=5),
                "value": range(5),
            }
        )
        dm.save(df1, "selic", subdir="daily")

        df2 = pd.DataFrame(
            {
                "date": pd.bdate_range("2024-02-01", periods=5),
                "value": range(100, 105),
            }
        )
        dm.append(df2, "selic", subdir="daily")

        # Isso DEVERIA funcionar, mas falha por cache stale
        result = dm.read("selic", subdir="daily")
        assert len(result) == 10


# =========================================================================
# get_last_date
# =========================================================================


class TestGetLastDate:
    """DataManager.get_last_date() retorna MAX(date) do arquivo."""

    def test_returns_max_date(self, data_dir: Path, ts_daily: pd.DataFrame) -> None:
        dm = _make_manager(data_dir)
        dm.save(ts_daily, "selic", subdir="daily")
        last = dm.get_last_date("selic", subdir="daily")
        assert last is not None
        expected_last = ts_daily["date"].max()
        assert pd.Timestamp(last) == pd.Timestamp(expected_last)

    def test_nonexistent_returns_none(self, data_dir: Path) -> None:
        dm = _make_manager(data_dir)
        assert dm.get_last_date("fantasma", subdir="daily") is None


# =========================================================================
# list_files / is_first_run
# =========================================================================


class TestListFiles:
    """DataManager.list_files() e is_first_run()."""

    def test_list_files_empty_dir(self, data_dir: Path) -> None:
        dm = _make_manager(data_dir)
        assert dm.list_files("daily") == []

    def test_list_files_nonexistent_dir(self, data_dir: Path) -> None:
        dm = _make_manager(data_dir)
        assert dm.list_files("nonexistent") == []

    def test_list_files_returns_stems(
        self, data_dir: Path, ts_daily: pd.DataFrame
    ) -> None:
        dm = _make_manager(data_dir)
        dm.save(ts_daily, "selic", subdir="daily")
        dm.save(ts_daily, "cdi", subdir="daily")
        files = dm.list_files("daily")
        assert set(files) == {"selic", "cdi"}

    def test_is_first_run_true_when_empty(self, data_dir: Path) -> None:
        dm = _make_manager(data_dir)
        assert dm.is_first_run("daily") is True

    def test_is_first_run_false_after_save(
        self, data_dir: Path, ts_daily: pd.DataFrame
    ) -> None:
        dm = _make_manager(data_dir)
        dm.save(ts_daily, "selic", subdir="daily")
        assert dm.is_first_run("daily") is False

    def test_is_first_run_nonexistent_dir(self, data_dir: Path) -> None:
        dm = _make_manager(data_dir)
        assert dm.is_first_run("nonexistent") is True


# =========================================================================
# get_metadata
# =========================================================================


class TestGetMetadata:
    """DataManager.get_metadata() retorna info basica do arquivo."""

    def test_returns_metadata(self, data_dir: Path, ts_daily: pd.DataFrame) -> None:
        dm = _make_manager(data_dir)
        dm.save(ts_daily, "selic", subdir="daily")
        meta = dm.get_metadata("selic", subdir="daily")
        assert meta is not None
        assert meta["arquivo"] == "selic"
        assert meta["registros"] == len(ts_daily)
        assert meta["status"] == "OK"

    def test_nonexistent_returns_none(self, data_dir: Path) -> None:
        dm = _make_manager(data_dir)
        assert dm.get_metadata("fantasma", subdir="daily") is None
