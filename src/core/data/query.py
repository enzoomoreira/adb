"""
Interface de consultas SQL via DuckDB.

Permite queries eficientes em arquivos Parquet sem carregar tudo em memoria.
Ideal para exploracao de dados e analises ad-hoc.
"""

from pathlib import Path

import pandas as pd
import duckdb


class QueryEngine:
    """
    Motor de consultas SQL sobre arquivos Parquet usando DuckDB.

    Responsabilidades:
    - Executar queries SQL em arquivos Parquet
    - Fornecer conexao DuckDB para queries avancadas
    - Leitura filtrada de dados (colunas, where)

    Para operacoes de persistencia (save/append), use DataManager.
    """

    def __init__(self, base_path: Path):
        """
        Inicializa o motor de consultas.

        Args:
            base_path: Caminho base para diretorio data/
        """
        self.base_path = Path(base_path)
        self.raw_path = self.base_path / 'raw'
        self.processed_path = self.base_path / 'processed'

    def sql(
        self,
        query: str,
        subdir: str = None,
    ) -> pd.DataFrame:
        """
        Executa query SQL nos arquivos parquet usando DuckDB.

        Permite consultas eficientes sem carregar todos os dados na memoria.
        Os paths podem ser especificados diretamente no SQL ou usar variaveis.

        Args:
            query: Query SQL. Pode usar:
                - Paths absolutos/relativos: 'data/raw/bacen/sgs/daily/*.parquet'
                - Glob patterns: '*.parquet'
                - Variavel {raw}: substitui pelo caminho raw/
                - Variavel {processed}: substitui pelo caminho processed/
                - Variavel {subdir}: substitui pelo subdir se fornecido
            subdir: Subdiretorio para substituir na variavel {subdir}

        Returns:
            DataFrame com resultado da query

        Examples:
            # Query direta com path
            qe.sql("SELECT * FROM 'data/raw/bacen/sgs/daily/selic.parquet' LIMIT 10")

            # Usando variaveis
            qe.sql("SELECT * FROM '{subdir}/selic.parquet'", subdir='bacen/sgs/daily')

            # Agregacao
            qe.sql('''
                SELECT strftime(date, '%Y') as ano, AVG(value) as media
                FROM '{raw}/bacen/sgs/daily/selic.parquet'
                GROUP BY ano
            ''')

            # Multiplos arquivos com glob
            qe.sql("SELECT * FROM '{raw}/mte/caged/cagedmov_2025-*.parquet'")
        """
        # Substituir variaveis no SQL
        query = query.replace('{raw}', str(self.raw_path))
        query = query.replace('{processed}', str(self.processed_path))
        if subdir:
            query = query.replace('{subdir}', str(self.raw_path / subdir))

        return duckdb.sql(query).df()

    def connection(self, subdir: str = None) -> duckdb.DuckDBPyConnection:
        """
        Retorna conexao DuckDB para queries avancadas.

        Util para queries complexas, transacoes ou quando precisa de mais controle.

        Args:
            subdir: Subdiretorio para registrar como variavel (opcional)

        Returns:
            Conexao DuckDB

        Example:
            con = qe.connection('bacen/sgs/daily')
            result = con.execute('''
                SELECT * FROM read_parquet('{}/*.parquet')
            '''.format(qe.raw_path / 'bacen/sgs/daily')).df()
        """
        con = duckdb.connect()

        # Registrar paths como variaveis para facilitar uso
        con.execute(f"SET VARIABLE raw_path = '{self.raw_path}'")
        con.execute(f"SET VARIABLE processed_path = '{self.processed_path}'")
        if subdir:
            con.execute(f"SET VARIABLE subdir_path = '{self.raw_path / subdir}'")

        return con

    def read(
        self,
        filename: str,
        subdir: str = 'daily',
        columns: list[str] = None,
        where: str = None,
    ) -> pd.DataFrame:
        """
        Le arquivo de dados com filtros opcionais via DuckDB.

        Mais eficiente que carregar o arquivo inteiro quando precisa
        apenas de algumas colunas ou linhas filtradas.

        Args:
            filename: Nome do arquivo (sem extensao)
            subdir: Subdiretorio dentro de raw/
            columns: Lista de colunas para carregar (None = todas)
            where: Clausula WHERE para filtrar dados (ex: "value > 10")

        Returns:
            DataFrame com dados filtrados (vazio se arquivo nao existe)

        Examples:
            # Apenas algumas colunas
            df = qe.read('selic', 'bacen/sgs/daily', columns=['value'])

            # Com filtro
            df = qe.read('selic', 'bacen/sgs/daily', where="value > 10")

            # Ambos
            df = qe.read('cagedmov_2025-01', 'mte/caged',
                         columns=['uf', 'salário', 'saldomovimentação'],
                         where="uf = 35")  # SP
        """
        filepath = self.raw_path / subdir / f"{filename}.parquet"

        if not filepath.exists():
            return pd.DataFrame()

        cols = ', '.join(columns) if columns else '*'
        sql = f"SELECT {cols} FROM '{filepath}'"
        if where:
            sql += f" WHERE {where}"

        return duckdb.sql(sql).df()

    def read_glob(
        self,
        pattern: str,
        subdir: str = None,
        columns: list[str] = None,
        where: str = None,
    ) -> pd.DataFrame:
        """
        Le multiplos arquivos usando glob pattern.

        Args:
            pattern: Glob pattern (ex: 'cagedmov_2025-*.parquet')
            subdir: Subdiretorio dentro de raw/ (opcional)
            columns: Lista de colunas para carregar (None = todas)
            where: Clausula WHERE para filtrar dados

        Returns:
            DataFrame com dados de todos os arquivos combinados

        Examples:
            # Todos os arquivos CAGED de 2025
            df = qe.read_glob('cagedmov_2025-*.parquet', subdir='mte/caged')

            # Com filtro
            df = qe.read_glob('cagedmov_*.parquet', subdir='mte/caged',
                              columns=['uf', 'saldomovimentação'],
                              where="uf = 35")
        """
        if subdir:
            full_pattern = str(self.raw_path / subdir / pattern)
        else:
            full_pattern = pattern

        cols = ', '.join(columns) if columns else '*'
        sql = f"SELECT {cols} FROM '{full_pattern}'"
        if where:
            sql += f" WHERE {where}"

        return duckdb.sql(sql).df()

    def aggregate(
        self,
        filename: str,
        subdir: str,
        group_by: str | list[str],
        agg: dict[str, str],
        where: str = None,
    ) -> pd.DataFrame:
        """
        Executa agregacao em um arquivo.

        Args:
            filename: Nome do arquivo (sem extensao, aceita glob)
            subdir: Subdiretorio dentro de raw/
            group_by: Coluna(s) para agrupar
            agg: Dict de {coluna: funcao} (ex: {'value': 'AVG', 'count': 'COUNT(*)'})
            where: Clausula WHERE opcional

        Returns:
            DataFrame com resultado da agregacao

        Examples:
            # Media de selic por ano
            df = qe.aggregate('selic', 'bacen/sgs/daily',
                              group_by='strftime(date, "%Y")',
                              agg={'value': 'AVG'})

            # Saldo CAGED por UF
            df = qe.aggregate('cagedmov_2025-*.parquet', 'mte/caged',
                              group_by='uf',
                              agg={'saldomovimentação': 'SUM'})
        """
        filepath = self.raw_path / subdir / filename
        if not filename.endswith('.parquet'):
            filepath = self.raw_path / subdir / f"{filename}.parquet"

        # Construir SELECT
        if isinstance(group_by, str):
            group_cols = group_by
        else:
            group_cols = ', '.join(group_by)

        agg_exprs = ', '.join([
            f"{func}({col}) as {col}" if func != 'COUNT(*)' else f"COUNT(*) as {col}"
            for col, func in agg.items()
        ])

        sql = f"SELECT {group_cols}, {agg_exprs} FROM '{filepath}'"
        if where:
            sql += f" WHERE {where}"
        sql += f" GROUP BY {group_cols}"

        return duckdb.sql(sql).df()
