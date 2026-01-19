"""
Coletor de dados IPEA.

Orquestra a coleta de series temporais do IPEADATA.
"""

from pathlib import Path

import pandas as pd

from adb.core.collectors import BaseCollector
from adb.core.utils import get_indicator_config
from .client import IPEAClient
from .indicators import IPEA_CONFIG


class IPEACollector(BaseCollector):
    """
    Orquestrador de coleta de dados IPEA (IPEADATA).

    API publica:
    - collect() - Coleta um ou mais indicadores usando config predefinida
    - consolidate() - Consolida arquivos em DataFrame unico
    - get_status() - Status dos arquivos salvos

    Herda de BaseCollector para logging padronizado e get_status().
    """

    default_subdir = 'ipea/monthly'

    def __init__(self, data_path: Path = None):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho para diretorio data/ (opcional, usa DATA_PATH se None)
        """
        super().__init__(data_path)
        self.client = IPEAClient()

    # =========================================================================
    # Metodo interno de coleta
    # =========================================================================

    def _collect_series(
        self,
        code: str,
        filename: str,
        name: str = None,
        frequency: str = "monthly",
        subdir: str = None,
        save: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Coleta uma serie temporal com controle total.

        Suporta atualizacao incremental: se ja existem dados salvos,
        busca apenas registros novos desde a ultima data.

        Args:
            code: Codigo IPEA da serie (ex: 'CAGED12_SALDON12')
            filename: Nome do arquivo para salvar (sem extensao)
            name: Nome da serie para logs (default: usa filename)
            frequency: 'daily', 'monthly' ou 'quarterly'
            subdir: Subdiretorio dentro de raw/ (default: ipea/{frequency})
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            DataFrame com dados coletados
        """
        name = name or filename
        subdir = subdir or f"ipea/{frequency}"

        def fetch(start_date: str | None) -> pd.DataFrame:
            return self.client.get_data(
                code=code,
                name=name,
                start_date=start_date,
                verbose=False,
            )

        # Para quarterly, usar monthly (DataManager pula para proximo mes)
        effective_freq = "monthly" if frequency == "quarterly" else frequency

        return self._collect_with_sync(
            fetch_fn=fetch,
            filename=filename,
            name=name,
            subdir=subdir,
            frequency=effective_freq,
            save=save,
            verbose=verbose,
        )

    # =========================================================================
    # API Publica
    # =========================================================================

    def collect(
        self,
        indicators: list[str] | str = "all",
        save: bool = True,
        verbose: bool = True,
    ) -> None:
        """
        Coleta um ou mais indicadores.

        Args:
            indicators: Indicadores a coletar:
                - 'all': todos de IPEA_CONFIG
                - lista: ['caged_saldo', 'caged_admissoes', ...]
                - string: 'caged_saldo' (um unico)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            Dict {indicator_key: DataFrame} com dados coletados
        """
        # Normalizar para lista
        keys = self._normalize_indicators_list(indicators, IPEA_CONFIG)

        self._log_collect_start(
            title="IPEA - Instituto de Pesquisa Economica Aplicada",
            num_indicators=len(keys),
            subdir=self.default_subdir,
            check_first_run=True,
            verbose=verbose,
        )

        for key in keys:
            config = get_indicator_config(IPEA_CONFIG, key)

            self._collect_series(
                code=config["code"],
                filename=key,
                name=config["name"],
                frequency=config["frequency"],
                save=save,
                verbose=verbose,
            )

            if verbose:
                print()

        self._log_collect_end(verbose=verbose)

