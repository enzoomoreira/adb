"""
Explorer Expectations - Interface pythonica para query de expectativas Focus.

Uso:
    from adb.core.data import expectations

    # Dados brutos (todas as colunas)
    df = expectations.read('ipca_anual')
    df = expectations.read('ipca_anual', start='2023')

    # Serie processada (pronta para plot)
    df = expectations.read('selic_anual', year=2027)       # Expectativa Selic fim 2027
    df = expectations.read('ipca_12m', smooth=True)        # IPCA 12m suavizado

    print(expectations.available())
"""

from typing import List

import pandas as pd

from adb.core.data.explorers import BaseExplorer
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
    no formato padrao (DatetimeIndex + coluna 'value'), compativel com outros explorers.
    """

    _CONFIG = EXPECTATIONS_CONFIG
    _SUBDIR = "bacen/expectations"
    _DATE_COLUMN = "date"

    @property
    def _COLLECTOR_CLASS(self):
        """Retorna a classe do coletor associado."""
        from adb.bacen.expectations.collector import ExpectationsCollector
        return ExpectationsCollector

    # =========================================================================
    # Metodos de leitura e processamento
    # =========================================================================

    def read(
        self,
        *indicators: str,
        start: str = None,
        end: str = None,
        columns: List[str] = None,
        year: int = None,
        smooth: bool = None,
        metric: str = 'Mediana',
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
            - Com year/smooth: serie processada (DatetimeIndex + coluna 'value')

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
        return self._process_to_series(df, year=year, smooth=smooth, metric=metric)

    def _process_to_series(
        self,
        df: pd.DataFrame,
        year: int = None,
        smooth: bool = None,
        metric: str = 'Mediana',
    ) -> pd.DataFrame:
        """
        Processa DataFrame bruto para serie temporal padrao.

        Aplica filtros (year, smooth), seleciona metrica e agrega duplicatas.
        """
        result = df.copy()

        # Filtro por ano de referencia (DataReferencia)
        if year is not None and 'DataReferencia' in result.columns:
            # DataReferencia pode ser int ou str dependendo da fonte
            result['DataReferencia'] = result['DataReferencia'].astype(str)
            result = result[result['DataReferencia'] == str(year)]

        # Filtro por serie suavizada
        if smooth is not None and 'Suavizada' in result.columns:
            flag = 'S' if smooth else 'N'
            result = result[result['Suavizada'] == flag]

        if result.empty:
            return pd.DataFrame(columns=['value'])

        # Seleciona metrica
        if metric not in result.columns:
            available = [c for c in result.columns if c in ['Mediana', 'Media', 'Minimo', 'Maximo']]
            raise ValueError(f"Metrica '{metric}' nao encontrada. Disponiveis: {available}")

        result = result[[metric]]

        # Agrega duplicatas por data (media)
        if result.index.duplicated().any():
            result = result.groupby(result.index).mean()

        # Renomeia para formato padrao
        result.columns = ['value']

        return result.sort_index()

    # =========================================================================
    # Metodos auxiliares
    # =========================================================================

    def _join_multiple(self, dfs: list, indicators: tuple) -> pd.DataFrame:
        """
        Override: Expectations concatena ao invés de join.
        
        Cada indicador pode ter estrutura diferente, entao concatenamos
        com uma coluna 'indicator' para identificar.
        """
        if not dfs:
            return pd.DataFrame()

        for df, ind in zip(dfs, indicators):
            df['indicator'] = ind

        return pd.concat(dfs, ignore_index=True)

    def collect(
        self,
        indicators: list[str] | str = 'all',
        start_date: str = None,
        limit: int = None,
        save: bool = True,
        verbose: bool = True,
    ) -> None:
        """
        Coleta expectativas do Relatorio Focus (BCB).

        Args:
            indicators: 'all', lista, ou string com indicador(es)
            start_date: Data inicial (formato 'YYYY-MM-DD')
            limit: Limite de registros
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso
        """
        collector = self._COLLECTOR_CLASS()
        collector.collect(
            indicators=indicators, 
            start_date=start_date, 
            limit=limit,
            save=save, 
            verbose=verbose
        )
