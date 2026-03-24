"""
Explorer Expectations - Interface pythonica para query de expectativas Focus.

Uso:
    import adb

    # Dados brutos (todas as colunas)
    df = adb.expectations.read('ipca_anual')
    df = adb.expectations.read('ipca_anual', start='2024')

    # Serie processada (pronta para plot)
    df = adb.expectations.read('selic_anual', year=2027)     # Expectativa Selic fim 2027
    df = adb.expectations.read('ipca_12m', smooth=True)      # IPCA 12m suavizado

    print(adb.expectations.available())
"""

import pandas as pd

from adb.domain.explorers import BaseExplorer
from .indicators import EXPECTATIONS_CONFIG


class ExpectationsExplorer(BaseExplorer):
    """
    Explorer para dados de Expectativas do BCB (Relatorio Focus).

    Fornece interface pythonica para leitura de expectativas
    de mercado do Banco Central do Brasil.

    Parametros especiais no read():
        year: Filtra por ano de referencia (DataReferencia) - para indicadores anuais
        smooth: Filtra por serie suavizada (Suavizada='S') - para indicadores de inflacao
        metric: Metrica a extrair ('Mediana', 'Media', 'Minimo', 'Maximo') - default 'Mediana'

    Quando year ou smooth sao passados, o resultado e agregado e retornado
    no formato padrao (DatetimeIndex + coluna com nome do indicador), compativel com outros explorers.
    """

    _CONFIG = EXPECTATIONS_CONFIG
    _SUBDIR = "bacen/expectations"
    _DATE_COLUMN = "date"

    @property
    def _COLLECTOR_CLASS(self):
        """Retorna a classe do coletor associado."""
        from adb.providers.bacen.expectations.collector import ExpectationsCollector

        return ExpectationsCollector

    # =========================================================================
    # Metodos de leitura e processamento
    # =========================================================================

    def read(
        self,
        *indicators: str,
        start: str | None = None,
        end: str | None = None,
        columns: list[str] | None = None,
        year: int | None = None,
        smooth: bool | None = None,
        metric: str = "Mediana",
    ) -> pd.DataFrame:
        """
        Le expectativas do Relatorio Focus.

        Args:
            *indicators: Nomes dos indicadores (ex: 'selic_anual', 'ipca_12m')
            start: Data inicial (formatos: '2020', '2020-01', '2020-01-01')
            end: Data final (mesmos formatos)
            columns: Colunas especificas (default: todas)
            year: Ano de referencia para filtrar (ex: 2027 para Selic fim de 2027)
            smooth: Se True, filtra apenas serie suavizada (Suavizada='S')
            metric: Metrica a extrair quando year/smooth sao usados
                    ('Mediana', 'Media', 'Minimo', 'Maximo'). Default: 'Mediana'

        Returns:
            DataFrame com expectativas.
            - Sem year/smooth: dados brutos com todas as colunas
            - Com year/smooth: serie processada (DatetimeIndex + coluna com nome do indicador)

        Examples:
            # Dados brutos
            df = expectations.read('selic_anual')

            # Expectativa Selic para fim de 2027
            df = expectations.read('selic_anual', year=2027)

            # IPCA 12m suavizado
            df = expectations.read('ipca_12m', smooth=True)

            # Media ao inves de Mediana
            df = expectations.read('ipca_12m', smooth=True, metric='Media')
        """
        # Busca dados brutos usando metodo da classe base
        df = super().read(*indicators, start=start, end=end, columns=columns)

        if df.empty:
            return df

        # Se nenhum filtro especial, retorna dados brutos
        if year is None and smooth is None:
            return df

        # Aplica filtros e processa para serie
        df = self._process_to_series(df, year=year, smooth=smooth, metric=metric)
        if len(indicators) == 1 and "value" in df.columns:
            df = df.rename(columns={"value": indicators[0]})
        return df

    def _process_to_series(
        self,
        df: pd.DataFrame,
        year: int | None = None,
        smooth: bool | None = None,
        metric: str = "Mediana",
    ) -> pd.DataFrame:
        """
        Processa DataFrame bruto para serie temporal padrao.

        Aplica filtros (year, smooth), seleciona metrica e agrega duplicatas.
        """
        result = df.copy()

        # Filtro por ano de referencia (DataReferencia)
        if year is not None and "DataReferencia" in result.columns:
            # DataReferencia pode ser int ou str dependendo da fonte
            result["DataReferencia"] = result["DataReferencia"].astype(str)
            result = result[result["DataReferencia"] == str(year)]

        # Filtro por serie suavizada
        if smooth is not None and "Suavizada" in result.columns:
            flag = "S" if smooth else "N"
            result = result[result["Suavizada"] == flag]

        if result.empty:
            return pd.DataFrame(columns=["value"])

        # Seleciona metrica
        if metric not in result.columns:
            available = [
                c
                for c in result.columns
                if c in ["Mediana", "Media", "Minimo", "Maximo"]
            ]
            raise ValueError(
                f"Metrica '{metric}' nao encontrada. Disponiveis: {available}"
            )

        result = result[[metric]]

        # Agrega duplicatas por data (media)
        if result.index.duplicated().any():
            result = result.groupby(result.index).mean()

        # Renomeia para formato padrao
        result.columns = ["value"]

        return result.sort_index()

    def _fetch_one(
        self, indicator: str, start: str | None, end: str | None
    ) -> pd.DataFrame:
        from adb.providers.bacen.expectations.client import ExpectationsClient

        config = self._CONFIG[indicator]
        client = ExpectationsClient()
        return client.query(
            endpoint_key=config["endpoint"],
            indicator=config.get("indicator"),
            start_date=start,
            end_date=end,
        )

    def fetch(
        self,
        *indicators: str,
        start: str | None = None,
        end: str | None = None,
        year: int | None = None,
        smooth: bool | None = None,
        metric: str = "Mediana",
    ) -> pd.DataFrame:
        """
        Busca expectativas diretamente da API (stateless, sem disco).

        Args:
            *indicators: Nomes dos indicadores (ex: 'selic_anual', 'ipca_12m')
            start: Data inicial
            end: Data final
            year: Ano de referencia para filtrar
            smooth: Se True, filtra apenas serie suavizada
            metric: Metrica a extrair ('Mediana', 'Media', 'Minimo', 'Maximo')
        """
        df = super().fetch(*indicators, start=start, end=end)

        if df.empty or (year is None and smooth is None):
            return df

        df = self._process_to_series(df, year=year, smooth=smooth, metric=metric)
        if len(indicators) == 1 and "value" in df.columns:
            df = df.rename(columns={"value": indicators[0]})
        return df

    # =========================================================================
    # Metodos auxiliares
    # =========================================================================

    def _join(self, dfs: list, indicators: tuple) -> pd.DataFrame:
        """
        Override: Expectations concatena ao invés de join.

        Cada indicador pode ter estrutura diferente, entao concatenamos
        com uma coluna 'indicator' para identificar.
        """
        if not dfs:
            return pd.DataFrame()

        for df, ind in zip(dfs, indicators):
            df["indicator"] = ind

        return pd.concat(dfs, ignore_index=True)
