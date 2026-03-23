"""
Interface de consultas para arquivos Parquet.

Design Simplificado (DuckDB-first):
- Usa DuckDB como motor único para leitura e consultas
- Aproveita o otimizador nativo do DuckDB para pushdown de filtros
- Elimina complexidade de parsing manual de SQL
"""

from pathlib import Path
import pandas as pd
import duckdb

from adb.shared.utils.dates import DATE_COLUMNS

# Logger lazy - so carrega quando usado
_logger = None


def _get_logger():
    """Logger lazy - so carrega quando usado."""
    global _logger
    if _logger is None:
        from adb.infra.log import get_logger

        _logger = get_logger(__name__)
    return _logger


class QueryEngine:
    """
    Motor de consultas unificado sobre arquivos Parquet.

    Simplificado para delegar a complexidade de otimização de queries
    para o DuckDB, mantendo uma interface Pythonica simples.
    """

    def __init__(self, base_path: Path | None = None, progress_bar: bool = False):
        """
        Inicializa o motor de consultas.

        Args:
            base_path: Caminho base para diretorio data/ (opcional, usa DATA_PATH se None)
            progress_bar: Se True, exibe barra de progresso do DuckDB (default: False)
        """
        from adb.infra.config import get_settings

        self.base_path = Path(base_path) if base_path else get_settings().data_path
        self.raw_path = self.base_path / "raw"
        self.processed_path = self.base_path / "processed"

        self._conn = duckdb.connect()
        self._conn.execute(f"SET enable_progress_bar = {str(progress_bar).lower()}")

    # =========================================================================
    # Helpers Internos
    # =========================================================================

    def _ensure_dates(
        self, path_or_glob: str, columns: list[str] | None
    ) -> list[str] | None:
        """
        Garante que colunas de data sejam incluídas na selecao para indexacao correta.
        """
        if not columns:
            return None  # Select *

        # Verifica se já solicitou alguma data
        columns_lower = {c.lower() for c in columns}
        if any(d.lower() in columns_lower for d in DATE_COLUMNS):
            return columns

        # Se não, precisamos descobrir se existe coluna de data no arquivo
        try:
            # DuckDB DESCRIBE é rápido
            schema_df = duckdb.sql(
                f"DESCRIBE SELECT * FROM '{path_or_glob}' LIMIT 0"
            ).df()
            available_cols = set(schema_df["column_name"].values)

            for date_col in DATE_COLUMNS:
                if date_col in available_cols:
                    return [date_col] + columns
        except Exception:
            # Em caso de erro (ex: glob vazio), retornamos as colunas originais
            # e deixamos o erro propagar na execução real se for o caso
            pass

        return columns

    def _query(
        self, source: str, columns: list[str] | None = None, where: str | None = None
    ) -> str:
        """Constroi a query SQL para o DuckDB."""

        # Selecao de colunas com garantia de data
        cols_to_select = self._ensure_dates(source, columns)
        select_clause = ", ".join(cols_to_select) if cols_to_select else "*"

        query = f"SELECT {select_clause} FROM '{source}'"

        if where:
            query += f" WHERE {where}"

        return query

    # =========================================================================
    # API de Leitura
    # =========================================================================

    def read(
        self,
        filename: str,
        subdir: str = "daily",
        columns: list[str] | None = None,
        where: str | None = None,
    ) -> pd.DataFrame:
        """
        Lê arquivo Parquet de forma eficiente.

        Args:
            filename: Nome do arquivo (sem extensão)
            subdir: Subdiretório dentro de raw/
            columns: Lista de colunas para carregar
            where: Filtro SQL (ex: "uf = 35 AND date >= '2023-01-01'")

        Returns:
            DataFrame Pandas (dados normalizados no save via Schema on Write).
        """
        filepath = self.raw_path / subdir / f"{filename}.parquet"

        if not filepath.exists():
            return pd.DataFrame()

        sql = self._query(str(filepath), columns, where)

        try:
            df = duckdb.sql(sql).df()
            return df
        except Exception as e:
            # Logar erro tecnicamente (nao exibir para usuario)
            _get_logger().error(f"Erro lendo {filename}: {e}")
            return pd.DataFrame()

    def read_glob(
        self,
        pattern: str,
        subdir: str | None = None,
        columns: list[str] | None = None,
        where: str | None = None,
    ) -> pd.DataFrame:
        """
        Lê múltiplos arquivos Parquet usando glob pattern.

        Args:
            pattern: Glob pattern (ex: 'cagedmov_2025-*.parquet')
            subdir: Subdiretório (opcional)
        """
        if subdir:
            full_pattern = str(self.raw_path / subdir / pattern)
        else:
            full_pattern = pattern

        try:
            if subdir and not list((self.raw_path / subdir).glob(pattern)):
                return pd.DataFrame()

            sql = self._query(full_pattern, columns, where)
            df = duckdb.sql(sql).df()
            # Nota: normalize_date_index é chamado apenas no save() (Schema on Write)
            return df
        except Exception:
            # Glob vazio ou erro de leitura
            return pd.DataFrame()

    def sql(self, query: str, subdir: str | None = None) -> pd.DataFrame:
        """
        Executa SQL arbitrário com substituição de variáveis de caminho.
        """
        # Substituir variaveis no SQL
        query = query.replace("{raw}", str(self.raw_path))
        query = query.replace("{processed}", str(self.processed_path))
        if subdir:
            query = query.replace("{subdir}", str(self.raw_path / subdir))

        return duckdb.sql(query).df()

    # =========================================================================
    # Agregacoes e Metadados
    # =========================================================================

    def aggregate(
        self,
        filename: str,
        subdir: str,
        group_by: str | list[str],
        agg: dict[str, str],
        where: str | None = None,
    ) -> pd.DataFrame:
        """
        Executa agregação otimizada.
        Args:
            agg: Dict {coluna: funcao} (ex: {'value': 'AVG'})
        """
        filepath = self.raw_path / subdir / filename
        if not filename.endswith(".parquet") and "*" not in filename:
            filepath = self.raw_path / subdir / f"{filename}.parquet"

        path_str = str(filepath)

        # Construir SELECT
        if isinstance(group_by, str):
            group_cols = group_by
        else:
            group_cols = ", ".join(group_by)

        agg_exprs = ", ".join(
            [
                f"{func}({col}) as {col}"
                if func.upper() != "COUNT(*)"
                else f"COUNT(*) as {col}"
                for col, func in agg.items()
            ]
        )

        sql = f"SELECT {group_cols}, {agg_exprs} FROM '{path_str}'"
        if where:
            sql += f" WHERE {where}"
        sql += f" GROUP BY {group_cols}"

        return duckdb.sql(sql).df()

    def get_metadata(self, filename: str, subdir: str) -> dict | None:
        """Retorna metadados básicos do arquivo."""
        filepath = self.raw_path / subdir / f"{filename}.parquet"
        if not filepath.exists():
            return None

        try:
            # DuckDB consegue ler metadata de parquet de forma eficiente
            # porem o COUNT(*) requer varredura de row groups (rapido, mas nao instantaneo)
            # Para metadata puro (k/v), pyarrow é melhor. Para estatisticas de dados, DuckDB.

            # 1. Discover date column
            schema = duckdb.sql(f"DESCRIBE SELECT * FROM '{filepath}' LIMIT 0").df()
            cols = set(schema["column_name"].tolist())

            date_col = "date" if "date" in cols else None

            # 2. Build Query
            if date_col:
                sql = f"SELECT COUNT(*) as total, MIN({date_col}) as min_date, MAX({date_col}) as max_date FROM '{filepath}'"
            else:
                sql = f"SELECT COUNT(*) as total, NULL as min_date, NULL as max_date FROM '{filepath}'"

            # 3. Execute
            res = duckdb.sql(sql).fetchone()
            assert res is not None
            total, min_d, max_d = res

            return {
                "arquivo": filename,
                "subdir": subdir,
                "registros": total,
                "colunas": len(cols),
                "primeira_data": pd.to_datetime(min_d) if min_d else None,
                "ultima_data": pd.to_datetime(max_d) if max_d else None,
                "status": "OK",
            }
        except Exception as e:
            return {"arquivo": filename, "status": "Erro", "error": str(e)}

    def connection(self) -> duckdb.DuckDBPyConnection:
        """Retorna uma conexão DuckDB configurada com variáveis de ambiente."""
        con = duckdb.connect()
        con.execute(f"SET VARIABLE raw_path = '{self.raw_path}'")
        con.execute(f"SET VARIABLE processed_path = '{self.processed_path}'")
        return con
