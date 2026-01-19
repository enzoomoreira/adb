"""
Coletor de expectativas do BCB (Relatorio Focus).

Orquestra a coleta de dados de expectativas com flexibilidade de parametros.
"""

from pathlib import Path
import pandas as pd

from adb.core.collectors import BaseCollector
from adb.core.utils import get_indicator_config
from .client import ExpectationsClient
from .indicators import EXPECTATIONS_CONFIG


class ExpectationsCollector(BaseCollector):
    """
    Orquestrador de coleta de expectativas do BCB (Relatorio Focus).

    API publica:
    - collect() - Coleta um ou mais indicadores usando config predefinida
    - consolidate() - Consolida arquivos em DataFrame unico
    - get_status() - Status dos arquivos salvos

    Herda de BaseCollector para logging padronizado e get_status().
    """

    default_subdir = 'bacen/expectations'

    def __init__(self, data_path: Path = None):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho base para diretorio data/ (opcional, usa DATA_PATH se None)
        """
        super().__init__(data_path)
        self.client = ExpectationsClient()

    # =========================================================================
    # Metodo interno de coleta
    # =========================================================================

    def _collect_endpoint(
        self,
        endpoint: str,
        filename: str,
        indicator: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = None,
        subdir: str = None,
        save: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Coleta dados de um endpoint com controle total.

        Suporta atualizacao incremental: se ja existem dados salvos,
        busca apenas registros novos desde a ultima data.

        Args:
            endpoint: Chave do endpoint ('top5_anuais', 'selic', etc)
            filename: Nome do arquivo para salvar (sem extensao)
            indicator: Filtrar por indicador (ex: 'IPCA')
            start_date: Data inicial 'YYYY-MM-DD' (override manual)
            end_date: Data final 'YYYY-MM-DD'
            limit: Limite de registros (None = sem limite)
            subdir: Subdiretorio dentro de raw/ (default: 'expectations')
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            DataFrame com dados coletados
        """
        subdir = subdir or self.default_subdir

        # Nome para log: usa indicator se disponivel, senao filename
        log_name = indicator or filename

        def fetch(auto_start_date: str | None) -> pd.DataFrame:
            # start_date manual tem prioridade sobre automatico
            effective_start = start_date or auto_start_date
            return self.client.query(
                endpoint_key=endpoint,
                indicator=indicator,
                start_date=effective_start,
                end_date=end_date,
                limit=limit,
            )

        return self._collect_with_sync(
            fetch_fn=fetch,
            filename=filename,
            name=log_name,
            subdir=subdir,
            frequency='daily', # Focus updates are effectively daily events
            save=save,
            verbose=verbose
        )

    # =========================================================================
    # API Publica
    # =========================================================================

    def collect(
        self,
        indicators: list[str] | str = 'all',
        start_date: str = None,
        limit: int = None,
        save: bool = True,
        verbose: bool = True,
    ) -> None:
        """
        Coleta um ou mais indicadores.

        Args:
            indicators: Indicadores a coletar:
                - 'all': todos de EXPECTATIONS_CONFIG
                - lista: ['ipca_anual', 'selic', ...]
                - string: 'ipca_anual' (um unico)
            start_date: Data inicial para todos (opcional)
            limit: Limite de registros para todos (opcional)
            save: Se True, salva cada indicador em Parquet
            verbose: Se True, imprime progresso

        Returns:
            Dict {key: DataFrame} com dados coletados
        """
        # Normalizar entrada
        keys = self._normalize_indicators_list(indicators, EXPECTATIONS_CONFIG)

        self._log_collect_start(
            title="BACEN - Expectativas (Relatorio Focus)",
            num_indicators=len(keys),
            subdir=self.default_subdir,
            check_first_run=True,
            verbose=verbose,
        )

        for key in keys:
            config = get_indicator_config(EXPECTATIONS_CONFIG, key)

            self._collect_endpoint(
                endpoint=config['endpoint'],
                filename=key,
                indicator=config['indicator'],
                start_date=start_date,
                limit=limit,
                subdir=self.default_subdir,
                save=save,
                verbose=verbose,
            )

            if verbose:
                print()

        self._log_collect_end(verbose=verbose)

