"""
Coletor de dados IBGE Sidra.

Orquestra a coleta de series temporais do Sistema IBGE de Recuperacao Automatica (SIDRA).
"""

import pandas as pd
from pathlib import Path

from adb.services.collectors import BaseCollector
from adb.shared.utils import get_config
from .client import SidraClient
from .indicators import SIDRA_CONFIG


class SidraCollector(BaseCollector):
    """
    Orquestrador de coleta de dados IBGE Sidra.

    API publica:
    - collect() - Coleta um ou mais indicadores usando config predefinida
    - get_status() - Status dos arquivos salvos

    Herda de BaseCollector para logging padronizado e get_status().
    """

    default_subdir = "ibge/sidra/monthly"

    def __init__(self, data_path: Path | None = None):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho para diretorio data/ (opcional, usa DATA_PATH se None)
        """
        super().__init__(data_path)
        self.client = SidraClient()

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
        Coleta um ou mais indicadores do IBGE Sidra.

        Args:
            indicators: Indicadores a coletar:
                - 'all': todos de SIDRA_CONFIG
                - lista: ['ipca', 'pib', ...]
                - string: 'ipca' (um unico)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso
        """
        keys = self._normalize_indicators(indicators, SIDRA_CONFIG)

        self._start(
            title="IBGE - Sistema SIDRA",
            num_indicators=len(keys),
            subdir=self.default_subdir,
            check_first_run=True,
            verbose=verbose,
        )

        for key in keys:
            config = get_config(SIDRA_CONFIG, key)
            frequency = self._get_frequency_for_file(key)
            subdir = f"ibge/sidra/{frequency}"

            # Logica de fetch
            def fetch(start_date: str | None) -> pd.DataFrame:
                return self.client.get_data(
                    config=config["parameters"],
                    start_date=start_date,
                )

            # Usa o metodo _sync do BaseCollector que ja trata
            # verificacao de existencia, delta update e salvamento.
            self._sync(
                fetch_fn=fetch,
                filename=key,
                name=config["name"],
                subdir=subdir,
                frequency=frequency,
                save=save,
                verbose=verbose,
            )

        self._end(verbose=verbose)

    def get_status(self, subdir: str | None = None) -> pd.DataFrame:
        """
        Retorna status dos arquivos IBGE Sidra.

        Agrega status dos diretorios monthly e quarterly.

        Returns:
            DataFrame com status de cada arquivo
        """
        dfs = []
        subdirs = ["ibge/sidra/monthly", "ibge/sidra/quarterly"]
        for subdir in subdirs:
            df = super().get_status(subdir)
            if not df.empty:
                dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        return pd.concat(dfs, ignore_index=True)

    def _get_frequency_for_file(self, filename: str) -> str:
        """
        Retorna a frequencia de um indicador IBGE Sidra.

        Args:
            filename: Nome do arquivo (chave em SIDRA_CONFIG)

        Returns:
            'monthly' ou 'quarterly'
        """
        config = SIDRA_CONFIG.get(filename, {})
        return config.get("frequency", "monthly")
