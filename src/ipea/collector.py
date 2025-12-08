"""
Coletor de dados IPEA.

Orquestra a coleta de series temporais do IPEADATA.
"""

from pathlib import Path

import pandas as pd

from core.data import DataManager
from .client import IPEAClient
from .indicators import IPEA_CONFIG, get_indicator_config


class IPEACollector:
    """
    Orquestrador de coleta de dados IPEA.

    Oferece dois niveis de uso:
    1. collect_series() - Controle total, usuario define codigo e filename
    2. collect() - Usa config predefinida, coleta um ou mais indicadores
    """

    def __init__(self, data_path: Path):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho para diretorio data/
        """
        self.data_path = Path(data_path)
        self.data_manager = DataManager(data_path)
        self.client = IPEAClient()

    # =========================================================================
    # NIVEL 1: Controle Total
    # =========================================================================

    def collect_series(
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
            if verbose:
                if start_date:
                    print(f"  Buscando {name} desde {start_date}...")
                else:
                    print(f"  Buscando {name} (historico completo)...")

            return self.client.get_data(
                code=code,
                name=name,
                start_date=start_date,
                verbose=verbose,
            )

        if save:
            # Para quarterly, usar monthly (DataManager pula para proximo mes)
            effective_freq = "monthly" if frequency == "quarterly" else frequency

            df, _ = self.data_manager.fetch_and_sync(
                filename=filename,
                subdir=subdir,
                fetch_fn=fetch,
                frequency=effective_freq,
                verbose=False,
            )
        else:
            df = fetch(None)

        if verbose and not df.empty:
            print(f"  {len(df):,} registros")

        return df

    # =========================================================================
    # NIVEL 2: API Simplificada
    # =========================================================================

    def collect(
        self,
        indicators: list[str] | str = "all",
        save: bool = True,
        verbose: bool = True,
    ) -> dict[str, pd.DataFrame]:
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
        if indicators == "all":
            keys = list(IPEA_CONFIG.keys())
        elif isinstance(indicators, str):
            keys = [indicators]
        else:
            keys = list(indicators)

        if verbose:
            print("=" * 70)
            print("IPEA - Instituto de Pesquisa Economica Aplicada")
            print(f"Indicadores a coletar: {len(keys)}")
            print("=" * 70)

        results = {}

        for key in keys:
            config = get_indicator_config(key)

            df = self.collect_series(
                code=config["code"],
                filename=key,
                name=config["name"],
                frequency=config["frequency"],
                save=save,
                verbose=verbose,
            )

            results[key] = df

        if verbose:
            print()
            print("Coleta concluida!")

        return results

    # =========================================================================
    # Consolidacao
    # =========================================================================

    def consolidate(
        self,
        subdir: str = "ipea/monthly",
        output_filename: str = "ipea_monthly_consolidated",
        save: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Consolida arquivos de um subdiretorio.

        Faz join horizontal dos arquivos por indice (data).

        Args:
            subdir: Subdiretorio a consolidar
            output_filename: Nome do arquivo consolidado
            save: Se True, salva em processed/
            verbose: Se True, imprime progresso

        Returns:
            DataFrame consolidado
        """
        if verbose:
            print("=" * 70)
            print("CONSOLIDANDO DADOS IPEA")
            print(f"Subdiretorio: {subdir}")
            print("=" * 70)

        df = self.data_manager.consolidate(
            subdir=subdir,
            output_filename=output_filename,
            save=save,
            verbose=verbose,
        )

        if verbose:
            if not df.empty:
                print(f"\nConsolidado: {len(df):,} registros, {len(df.columns)} colunas")
            print("Consolidacao concluida!")

        return df

    # =========================================================================
    # Status
    # =========================================================================

    def get_status(self, subdir: str = "ipea/monthly") -> pd.DataFrame:
        """
        Retorna status dos arquivos salvos.

        Args:
            subdir: Subdiretorio a verificar

        Returns:
            DataFrame com status de cada arquivo
        """
        files = self.data_manager.list_files(subdir)

        if not files:
            return pd.DataFrame()

        status_data = []
        for filename in files:
            df = self.data_manager.read(filename, subdir)

            if df.empty:
                status_data.append({
                    "arquivo": filename,
                    "registros": 0,
                    "primeira_data": None,
                    "ultima_data": None,
                    "status": "Vazio",
                })
            else:
                primeira_data = None
                ultima_data = None

                # Verificar se indice e datetime
                if pd.api.types.is_datetime64_any_dtype(df.index):
                    primeira_data = df.index.min()
                    ultima_data = df.index.max()

                status_data.append({
                    "arquivo": filename,
                    "registros": len(df),
                    "primeira_data": primeira_data,
                    "ultima_data": ultima_data,
                    "status": "OK",
                })

        return pd.DataFrame(status_data)
