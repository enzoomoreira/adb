"""
Explorer CAGED - Interface pythonica para query de microdados.

Uso:
    from core.data import caged

    df = caged.read(year=2025)
    df = caged.read(year=2025, month=10, uf=35)
    df = caged.saldo_por_uf(year=2025)
    df = caged.saldo_mensal(year=2025)

Otimizacao:
    - Leituras (read): QueryEngine com PyArrow (eficiente em memoria)
    - Agregacoes (saldo_*): QueryEngine com DuckDB (streaming)
"""

from typing import List
import pandas as pd

from .indicators import CAGED_CONFIG


class CAGEDExplorer:
    """
    Explorer para microdados CAGED.

    Fornece interface pythonica para leitura e agregacao de microdados
    do Cadastro Geral de Empregados e Desempregados.
    """

    _SUBDIR = "mte/caged"

    def __init__(self, query_engine=None):
        """
        Inicializa o explorer CAGED.

        Args:
            query_engine: QueryEngine customizado (opcional, cria novo se None)
        """
        from core.data import QueryEngine
        self._qe = query_engine or QueryEngine()

    def read(
        self,
        year: int,
        month: int = None,
        dataset: str = "cagedmov",
        uf: int = None,
        columns: List[str] = None,
        where: str = None,
    ) -> pd.DataFrame:
        """
        Le microdados CAGED.

        Args:
            year: Ano de referencia (2020+)
            month: Mes (1-12). None = todos os meses do ano.
            dataset: 'cagedmov', 'cagedfor', 'cagedexc'
            uf: Codigo UF para filtrar (35=SP, 33=RJ, etc)
            columns: Colunas especificas
            where: Clausula WHERE adicional

        Returns:
            DataFrame com microdados

        Examples:
            >>> caged.read(year=2025)
            >>> caged.read(year=2025, month=10)
            >>> caged.read(year=2025, uf=35, columns=['uf', 'salario'])
        """
        if dataset not in CAGED_CONFIG:
            available = ', '.join(CAGED_CONFIG.keys())
            raise ValueError(f"Dataset '{dataset}' invalido. Disponiveis: {available}")

        if year < 2020:
            raise ValueError("Novo CAGED disponivel apenas a partir de 2020")

        # Construir WHERE
        where_parts = []
        if uf is not None:
            where_parts.append(f"uf = {uf}")
        if where:
            where_parts.append(f"({where})")
        combined_where = " AND ".join(where_parts) if where_parts else None

            # Arquivo unico ou glob
        if month is not None:
            filename = f"{dataset}_{year}-{month:02d}"
            df = self._qe.read(filename, self._SUBDIR, columns=columns, where=combined_where)
        else:
            pattern = f"{dataset}_{year}-*.parquet"
            df = self._qe.read_glob(pattern, self._SUBDIR, columns=columns, where=combined_where)

        # Tratamento automatico de colunas numericas com virgula (padrao brasileiro)
        # Colunas comuns no CAGED que precisam de conversao
        numeric_cols = ['salário', 'horascontratuais', 'valor', 'salariomovimentacao']
        
        if not df.empty:
            for col in numeric_cols:
                if col in df.columns and df[col].dtype == 'object':
                    try:
                        # Substituir virgula por ponto e converter para float
                        df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except Exception:
                        pass # Falha silenciosa, mantem original
        
        return df

    def saldo_por_uf(
        self,
        year: int,
        month: int = None,
        dataset: str = "cagedmov",
    ) -> pd.DataFrame:
        """
        Calcula saldo de empregos por UF.

        Args:
            year: Ano de referencia
            month: Mes (None = ano inteiro)
            dataset: Tipo de dados

        Returns:
            DataFrame com saldo por UF

        Examples:
            >>> caged.saldo_por_uf(year=2025)
            >>> caged.saldo_por_uf(year=2025, month=10)
        """
        pattern = self._build_pattern(dataset, year, month)
        filepath = self._qe.raw_path / self._SUBDIR / pattern

        return self._qe.sql(f"""
            SELECT
                uf,
                SUM(saldomovimentação) as saldo,
                COUNT(*) as registros
            FROM '{filepath}'
            GROUP BY uf
            ORDER BY saldo DESC
        """)

    def saldo_mensal(
        self,
        year: int,
        uf: int = None,
        dataset: str = "cagedmov",
    ) -> pd.DataFrame:
        """
        Calcula saldo de empregos mensal.

        Args:
            year: Ano de referencia
            uf: Filtrar por UF (None = Brasil)
            dataset: Tipo de dados

        Returns:
            DataFrame com saldo por mes

        Examples:
            >>> caged.saldo_mensal(year=2025)
            >>> caged.saldo_mensal(year=2025, uf=35)  # Sao Paulo
        """
        pattern = f"{dataset}_{year}-*.parquet"
        filepath = self._qe.raw_path / self._SUBDIR / pattern
        where = f"WHERE uf = {uf}" if uf else ""

        return self._qe.sql(f"""
            SELECT
                CAST(competênciamov / 100 AS INTEGER) as ano,
                CAST(competênciamov % 100 AS INTEGER) as mes,
                SUM(saldomovimentação) as saldo,
                COUNT(*) as registros
            FROM '{filepath}'
            {where}
            GROUP BY 1, 2
            ORDER BY 1, 2
        """)
        
        # UX: Converter para datetime e indice real
        if not df.empty:
            df['date'] = pd.to_datetime(
                df['ano'].astype(str) + '-' + df['mes'].astype(str) + '-01'
            )
            df = df.set_index('date').sort_index()
            
        return df

    def saldo_por_setor(
        self,
        year: int,
        month: int = None,
        uf: int = None,
        dataset: str = "cagedmov",
    ) -> pd.DataFrame:
        """
        Calcula saldo por setor economico (secao CNAE).

        Args:
            year: Ano de referencia
            month: Mes (None = ano inteiro)
            uf: Filtrar por UF (None = Brasil)
            dataset: Tipo de dados

        Returns:
            DataFrame com saldo por setor

        Examples:
            >>> caged.saldo_por_setor(year=2025)
            >>> caged.saldo_por_setor(year=2025, uf=35)
        """
        pattern = self._build_pattern(dataset, year, month)
        filepath = self._qe.raw_path / self._SUBDIR / pattern
        where = f"WHERE uf = {uf}" if uf else ""

        return self._qe.sql(f"""
            SELECT
                seção as setor,
                SUM(saldomovimentação) as saldo,
                COUNT(*) as registros
            FROM '{filepath}'
            {where}
            GROUP BY seção
            ORDER BY saldo DESC
        """)

    def available_periods(self, dataset: str = "cagedmov") -> list[tuple]:
        """
        Retorna periodos (ano, mes) disponiveis.

        Args:
            dataset: Tipo de dados ('cagedmov', 'cagedfor', 'cagedexc')

        Returns:
            Lista de tuplas (ano, mes)

        Examples:
            >>> caged.available_periods()
            [(2020, 1), (2020, 2), ..., (2025, 10)]
        """
        data_path = self._qe.raw_path / self._SUBDIR
        periods = []

        for f in data_path.glob(f"{dataset}_*.parquet"):
            try:
                parts = f.stem.split("_")[1].split("-")
                periods.append((int(parts[0]), int(parts[1])))
            except (IndexError, ValueError):
                continue

        return sorted(periods)

    def info(self, dataset: str = None) -> dict:
        """
        Retorna informacoes sobre dataset(s).

        Args:
            dataset: Nome do dataset. None = todos.

        Returns:
            Dict com informacoes do(s) dataset(s)

        Examples:
            >>> caged.info('cagedmov')
            {'prefix': 'CAGEDMOV', 'name': 'Movimentacoes', ...}
        """
        if dataset:
            if dataset not in CAGED_CONFIG:
                raise KeyError(f"Dataset '{dataset}' nao encontrado")
            return CAGED_CONFIG[dataset].copy()
        return CAGED_CONFIG.copy()

    @staticmethod
    def _build_pattern(dataset: str, year: int, month: int = None) -> str:
        """
        Constroi pattern de arquivo.

        Args:
            dataset: Tipo de dados
            year: Ano
            month: Mes (opcional)

        Returns:
            Pattern de arquivo (ex: 'cagedmov_2025-*.parquet')
        """
        if month is not None:
            return f"{dataset}_{year}-{month:02d}.parquet"
        return f"{dataset}_{year}-*.parquet"
