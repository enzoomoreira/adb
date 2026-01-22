"""
Explorer CAGED - Interface pythonica para query de microdados.

Uso:
    from adb.core.data import caged

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

from adb.core.data.explorers import BaseExplorer
from .indicators import CAGED_CONFIG


class CAGEDExplorer(BaseExplorer):
    """
    Explorer para microdados CAGED.

    Fornece interface pythonica para leitura e agregacao de microdados
    do Cadastro Geral de Empregados e Desempregados.
    
    Nota: CAGED tem API diferente dos outros explorers (usa year/month).
    """

    _CONFIG = CAGED_CONFIG
    _SUBDIR = "mte/caged"

    @property
    def _COLLECTOR_CLASS(self):
        from adb.mte.caged.collector import CAGEDCollector
        return CAGEDCollector

    # =========================================================================
    # Override: CAGED tem API diferente (year/month ao inves de start/end)
    # =========================================================================

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
        """
        if dataset not in self._CONFIG:
            available = ', '.join(self._CONFIG.keys())
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

        # Nota: Colunas numéricas (salario, horascontratuais, salariomovimentacao)
        # são limpas no CAGEDCollector durante a ingestão (CSV→Parquet)

        return df

    # =========================================================================
    # Metodos especificos do CAGED (agregacoes SQL)
    # =========================================================================

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

    def collect(
        self,
        indicators: list[str] | str = "all",
        save: bool = True,
        verbose: bool = True,
        max_workers: int = 4,
    ) -> None:
        """
        Coleta microdados CAGED do MTE.

        Args:
            indicators: 'all', lista, ou string com dataset(s)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso
            max_workers: Threads para download paralelo
        """
        collector = self._COLLECTOR_CLASS()
        collector.collect(
            indicators=indicators, 
            save=save, 
            verbose=verbose, 
            max_workers=max_workers
        )

    @staticmethod
    def _build_pattern(dataset: str, year: int, month: int = None) -> str:
        """Constroi pattern de arquivo."""
        if month is not None:
            return f"{dataset}_{year}-{month:02d}.parquet"
        return f"{dataset}_{year}-*.parquet"
