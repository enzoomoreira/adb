import pandas as pd
from typing import Callable

from bcb import Expectativas

from adb.core.log import get_logger
from adb.core.resilience import retry
from .indicators import ENDPOINTS


class ExpectationsClient:
    """
    Cliente para a API de Expectativas do BCB (Relatorio Focus).
    """

    def __init__(self):
        """Inicializa o cliente de Expectativas."""
        self._api = Expectativas()
        self.logger = get_logger(self.__class__.__name__)

    # =========================================================================
    # Metodos Publicos
    # =========================================================================

    def get_endpoint(self, endpoint_key: str):
        """
        Retorna objeto endpoint para queries customizadas.

        Args:
            endpoint_key: Chave do endpoint (ex: 'top5_anuais', 'selic')

        Returns:
            Objeto Endpoint para construir queries OData
        """
        endpoint_name = ENDPOINTS.get(endpoint_key, endpoint_key)
        return self._api.get_endpoint(endpoint_name)

    @retry()  # usa defaults para falhas de rede
    def query(
        self,
        endpoint_key: str,
        indicator: str = None,
        start_date: str = None,
        end_date: str = None,
        reference_year: int = None,
        limit: int = None,
        select_columns: list[str] = None,
    ) -> pd.DataFrame:
        """
        Busca expectativas com filtros.

        Args:
            endpoint_key: Chave do endpoint ('top5_anuais', 'anuais', 'selic', etc)
            indicator: Filtrar por indicador (ex: 'IPCA', 'Selic')
            start_date: Data inicial da pesquisa 'YYYY-MM-DD'
            end_date: Data final da pesquisa 'YYYY-MM-DD'
            reference_year: Ano de referencia da projecao
            limit: Limite de registros
            select_columns: Lista de colunas para retornar

        Returns:
            DataFrame com as expectativas
        """
        try:
            ep = self.get_endpoint(endpoint_key)
            q = ep.query()

            if indicator:
                q = q.filter(ep.Indicador == indicator)

            if start_date:
                q = q.filter(ep.Data >= start_date)

            if end_date:
                q = q.filter(ep.Data <= end_date)

            if reference_year:
                q = q.filter(ep.DataReferencia == reference_year)

            if select_columns:
                cols = [getattr(ep, col) for col in select_columns]
                q = q.select(*cols)

            if limit:
                q = q.limit(limit)

            q = q.orderby(ep.Data.desc())

            return q.collect()

        except Exception as e:
            self.logger.error(f"Erro ao buscar expectativas: {e}")
            return pd.DataFrame()

    @retry()  # usa defaults para falhas de rede
    def raw_query(
        self,
        endpoint_key: str,
        filter_func: Callable = None,
        select_func: Callable = None,
        orderby_func: Callable = None,
        limit: int = None
    ) -> pd.DataFrame:
        """
        Query customizada com funcoes lambda para maior flexibilidade.

        Args:
            endpoint_key: Chave do endpoint
            filter_func: Funcao lambda(ep) que retorna expressao de filtro
            select_func: Funcao lambda(ep) que retorna tupla de colunas
            orderby_func: Funcao lambda(ep) que retorna expressao de ordenacao
            limit: Limite de registros

        Returns:
            DataFrame com resultados

        Example:
            df = client.raw_query(
                'top5_anuais',
                filter_func=lambda ep: (ep.Indicador == 'IPCA') & (ep.Data >= '2024-01-01'),
                select_func=lambda ep: (ep.Data, ep.Media, ep.Mediana),
                orderby_func=lambda ep: ep.Data.desc(),
                limit=100
            )
        """
        try:
            ep = self.get_endpoint(endpoint_key)
            q = ep.query()

            if filter_func:
                q = q.filter(filter_func(ep))

            if select_func:
                q = q.select(*select_func(ep))

            if orderby_func:
                q = q.orderby(orderby_func(ep))

            if limit:
                q = q.limit(limit)

            return q.collect()

        except Exception as e:
            self.logger.error(f"Erro na query customizada: {e}")
            return pd.DataFrame()
