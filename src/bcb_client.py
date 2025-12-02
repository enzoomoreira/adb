from bcb import sgs
from bcb import Expectativas
import pandas as pd

class BCBClient:
    """
    Client to interact with Banco Central do Brasil APIs using python-bcb library.
    """

    def __init__(self):
        self.expectativas = Expectativas()

    def get_sgs_data(self, codes: dict, start_date: str = None, end_date: str = None, last: int = None) -> pd.DataFrame:
        """
        Fetch Time Series from SGS (Sistema Gerenciador de Séries Temporais).

        Args:
            codes (dict): Dictionary where keys are names and values are SGS codes.
            start_date (str, optional): Start date in 'YYYY-MM-DD' format.
            end_date (str, optional): End date in 'YYYY-MM-DD' format.
            last (int, optional): Number of last records to fetch.

        Returns:
            pd.DataFrame: DataFrame with the requested series.
        """
        try:
            # sgs.get handles dict of codes nicely, renaming columns to keys
            df = sgs.get(codes, start=start_date, end=end_date, last=last)
            return df
        except Exception as e:
            print(f"Error fetching SGS data: {e}")
            return pd.DataFrame()

    def get_endpoint(self, endpoint: str):
        """
        Get an endpoint object for advanced OData queries.

        Args:
            endpoint (str): The endpoint name (e.g., 'ExpectativasMercadoTop5Anuais').

        Returns:
            Endpoint object for building custom queries.

        Example:
            ep = client.get_endpoint('ExpectativasMercadoTop5Anuais')
            df = ep.query().filter(ep.Indicador == 'IPCA').limit(10).collect()
        """
        return self.expectativas.get_endpoint(endpoint)

    def get_focus_expectations(
        self,
        endpoint: str = 'ExpectativasMercadoTop5Anuais',
        filter_func=None,
        select_func=None,
        limit: int = None,
        orderby_func=None
    ) -> pd.DataFrame:
        """
        Fetch Focus Report Expectations with support for OData query parameters.

        Args:
            endpoint (str): The endpoint to query (e.g., 'ExpectativasMercadoTop5Anuais').
            filter_func (callable, optional): Function that receives the endpoint and returns filter expression.
                Example: lambda ep: ep.Indicador == 'IPCA'
            select_func (callable, optional): Function that receives the endpoint and returns columns to select.
                Example: lambda ep: (ep.Data, ep.Media, ep.Mediana)
            limit (int, optional): Limit number of records returned.
            orderby_func (callable, optional): Function that receives the endpoint and returns orderby expression.
                Example: lambda ep: ep.Data.desc()

        Returns:
            pd.DataFrame: DataFrame with the requested expectations.

        Example:
            df = client.get_focus_expectations(
                endpoint='ExpectativasMercadoTop5Anuais',
                filter_func=lambda ep: ep.Indicador == 'IPCA',
                limit=10,
                orderby_func=lambda ep: ep.Data.desc()
            )
        """
        try:
            ep = self.expectativas.get_endpoint(endpoint)
            query = ep.query()

            # Apply filter if provided
            if filter_func:
                filter_expression = filter_func(ep)
                query = query.filter(filter_expression)

            # Apply select if provided
            if select_func:
                select_cols = select_func(ep)
                query = query.select(*select_cols)

            # Apply limit if provided
            if limit:
                query = query.limit(limit)

            # Apply orderby if provided
            if orderby_func:
                orderby_expression = orderby_func(ep)
                query = query.orderby(orderby_expression)

            return query.collect()
        except Exception as e:
            print(f"Error fetching Focus expectations: {e}")
            return pd.DataFrame()
