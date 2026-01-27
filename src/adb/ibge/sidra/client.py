"""
Cliente para a API do IBGE Sidra.
"""

import pandas as pd
import requests
from datetime import datetime

from adb.core.config import DEFAULT_REQUEST_TIMEOUT
from adb.core.log import get_logger
from adb.core.resilience import retry

class SidraClient:
    """
    Cliente para a API do IBGE Sidra.

    Adapta a logica de extracao padrao do repositorio para metodos
    estruturados e tipados.
    """

    def __init__(self):
        """Inicializa o cliente Sidra."""
        self.logger = get_logger(self.__class__.__name__)

    # =========================================================================
    # Metodos Publicos
    # =========================================================================

    def get_data(
        self,
        config: dict,
        start_date: str = None,
        verbose: bool = False
    ) -> pd.DataFrame:
        """
        Busca serie temporal do Sidra de acordo com configuracao.

        Args:
            config: Parte 'parameters' do SIDRA_CONFIG
            start_date: Data inicial 'YYYY-MM-DD' (filtra direto na API)
            verbose: Se True, imprime logs

        Returns:
            DataFrame com serie temporal (index=Date, value=valor)
        """
        params = config.copy()

        frequency = params.get('frequency', 'monthly')
        if start_date is not None:
            periodo_inicio = self._date_to_sidra_period(start_date, frequency)
            periodo_fim = self._date_to_sidra_period(datetime.now().strftime('%Y-%m-%d'), frequency)
            params['periodos'] = f"{periodo_inicio}-{periodo_fim}"

        data = self._request_data(**params)
        if not data:
            return pd.DataFrame()

        return self._format_data(data, params)

    # =========================================================================
    # Metodos Internos (Helpers)
    # =========================================================================

    def _date_to_sidra_period(self, date_str: str, frequency: str) -> str:
        """
        Converte data 'YYYY-MM-DD' para formato de periodo SIDRA.
        
        Args:
            date_str: Data no formato 'YYYY-MM-DD'
            frequency: 'monthly' ou 'quarterly'
            
        Returns:
            Periodo SIDRA: 'AAAAMM' para mensal, 'AAAA0T' para trimestral
        """
        dt = pd.to_datetime(date_str)
        
        if frequency == 'quarterly':
            # Trimestre: 1-3=01, 4-6=02, 7-9=03, 10-12=04
            quarter = (dt.month - 1) // 3 + 1
            return f"{dt.year:04d}{quarter:02d}"
        else:
            # Mensal: AAAAMM
            return f"{dt.year:04d}{dt.month:02d}"

    @retry()  # usa defaults de NETWORK_EXCEPTIONS, attempts, delay
    def _request_data(
        self,
        agregados: str,
        periodos: str,
        variaveis: str,
        nivel_territorial: str,
        localidades: str,
        classificador: str = None,
        **kwargs  # Ignora extras
    ) -> dict:
        """Realiza a request para a API do Sidra."""

        # URL Builder logic a partir do scrape original
        if classificador is None:
            url = (
                f"https://servicodados.ibge.gov.br/api/v3/agregados/{agregados}"
                f"/periodos/{periodos}/variaveis/{variaveis}"
                f"?localidades=N{nivel_territorial}[{localidades}]"
            )

            # Support for standard API classification filtering
            classification = kwargs.get('classification') or kwargs.get('classificacao')
            if classification:
                url += f"&classificacao={classification}"

        else:
            # Fallback/Alternative endpoint logic
            url = (
                f"https://apisidra.ibge.gov.br/values/t/{agregados}/v/all"
                f"/p/{periodos}/{classificador}/{variaveis}"
                f"/n{nivel_territorial}/{localidades}?formato=json"
            )

        response = requests.get(url, timeout=DEFAULT_REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def _format_data(self, data: list, params: dict) -> pd.DataFrame:
        """Formata os dados brutos da API para DataFrame padrao."""
        try:
            # Estrutura padrao da API v3:
            # Lista de dicts. Metadata pode estar no [0] ou ser lista plana dependendo do endpoint.
            
            if isinstance(data, list) and len(data) > 0 and 'resultados' in data[0]:
                 # Estrutura v3
                 results = data[0]['resultados']
                 if not results:
                     return pd.DataFrame()
                 
                 series_data = results[0]['series'][0]['serie']
                 # Dict { "AAAAMM": "valor", ... }
                 
                 df = pd.DataFrame(list(series_data.items()), columns=["date_raw", "value"])
                 
            else:
                 return pd.DataFrame()

            # Limpeza
            df = df.dropna()
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            
            # Tratamento de data
            # A API retorna AAAAMM para mensal e AAAA0T para trimestral
            frequency = params.get('frequency', 'monthly')
            
            if frequency == 'quarterly':
                # Converte para YYYY-Q1
                try:
                    df['year'] = df['date_raw'].str[:4]
                    df['quarter'] = df['date_raw'].str[4:].astype(int)
                    
                    # Cria PeriodIndex ("202401" -> "2024Q1")
                    df['date_period'] = pd.PeriodIndex(df['year'] + 'Q' + df['quarter'].astype(str), freq='Q')
                    
                    # Converte para fim do trimestre (timestamp)
                    df['date'] = df['date_period'].dt.to_timestamp(how='end')
                    df = df.drop(columns=['year', 'quarter', 'date_period'])
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao processar datas trimestrais: {e}")
                    df["date"] = pd.to_datetime(df["date_raw"], errors="coerce", format="%Y%m")

            else: # monthly default
                df["date"] = pd.to_datetime(df["date_raw"], errors="coerce", format="%Y%m")
                # Fim do mes
                df["date"] = df["date"] + pd.offsets.MonthEnd(0)
            
            df = df.set_index("date")
            df = df[['value']].sort_index()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao formatar dados IBGE: {e}")
            return pd.DataFrame()
