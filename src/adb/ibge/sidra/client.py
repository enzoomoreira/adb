"""
Cliente para a API do IBGE Sidra.
"""

import pandas as pd
import requests
from datetime import datetime

class SidraClient:
    """
    Cliente para a API do IBGE Sidra.

    Adapta a logica de extracao padrao do repositorio para metodos
    estruturados e tipados.
    """

    def __init__(self):
        """Inicializa o cliente Sidra."""
        pass

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
        
        # Converte start_date para formato de periodo SIDRA se especificado
        frequency = params.get('frequency', 'monthly')
        if start_date is not None:
            periodo_inicio = self._date_to_sidra_period(start_date, frequency)
            # Calcula periodo final baseado na data atual
            periodo_fim = self._date_to_sidra_period(datetime.now().strftime('%Y-%m-%d'), frequency)
            params['periodos'] = f"{periodo_inicio}-{periodo_fim}"
        
        data = self._request_data(**params)
        if not data:
             return pd.DataFrame()
             
        df = self._format_data(data, params)
        
        return df

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

    def _request_data(
        self,
        agregados: str,
        periodos: str,
        variaveis: str,
        nivel_territorial: str,
        localidades: str,
        classificador: str = None,
        **kwargs # Ignora extras
    ) -> dict:
        """Realiza a request para a API do Sidra."""
        
        # URL Builder logic a partir do scrape original
        if classificador is None:
             url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{agregados}/periodos/{periodos}/variaveis/{variaveis}?localidades=N{nivel_territorial}[{localidades}]"
             
             # Support for standard API classification filtering
             classification = kwargs.get('classification') or kwargs.get('classificacao')
             if classification:
                 url += f"&classificacao={classification}"
                 
        else:
            # Fallback/Alternative endpoint logic
            url = f"https://apisidra.ibge.gov.br/values/t/{agregados}/v/all/p/{periodos}/{classificador}/{variaveis}/n{nivel_territorial}/{localidades}?formato=json"

        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erro ao buscar dados IBGE Sidra: {e}")
            return {}

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
                    print(f"Erro ao processar datas trimestrais: {e}. Raw examples: {df['date_raw'].head().tolist()}")
                    df["date"] = pd.to_datetime(df["date_raw"], errors="coerce", format="%Y%m")

            else: # monthly default
                df["date"] = pd.to_datetime(df["date_raw"], errors="coerce", format="%Y%m")
                # Fim do mes
                df["date"] = df["date"] + pd.offsets.MonthEnd(0)
            
            df = df.set_index("date")
            df = df[['value']].sort_index()
            
            return df
            
        except Exception as e:
            print(f"Erro ao formatar dados IBGE: {e}")
            return pd.DataFrame()
