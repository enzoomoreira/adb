"""
Coletor de dados SGS do BCB.

Orquestra a coleta de series temporais com flexibilidade de parametros.
"""

from pathlib import Path
import pandas as pd

from ..base import BaseCollector
from .client import SGSClient
from .indicators import SGS_CONFIG, get_indicator_config


class SGSCollector(BaseCollector):
    """
    Orquestrador de coleta de dados SGS.

    Oferece dois niveis de uso:
    1. collect_series() - Controle total, usuario define codigo SGS e filename
    2. collect() - Usa config predefinida, coleta um ou mais indicadores

    Herda de BaseCollector:
    - save(), read(), list_files() - delegacoes para DataManager
    - get_status() - status dos arquivos salvos
    """

    default_subdir = 'sgs/daily'
    default_consolidate_subdirs = ['sgs/daily', 'sgs/monthly']

    def __init__(self, data_path: Path):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho para diretorio data/
        """
        super().__init__(data_path)
        self.client = SGSClient()

    # =========================================================================
    # NIVEL 1: Controle Total
    # =========================================================================

    def collect_series(
        self,
        code: int,
        filename: str,
        name: str = None,
        frequency: str = 'daily',
        subdir: str = None,
        save: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Coleta uma serie temporal com controle total.

        Args:
            code: Codigo SGS do indicador
            filename: Nome do arquivo para salvar (sem extensao)
            name: Nome da serie (default: usa filename)
            frequency: 'daily' ou 'monthly' (para chunking)
            subdir: Subdiretorio dentro de raw/ (default: usa frequency)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            DataFrame com dados coletados
        """
        if name is None:
            name = filename
        if subdir is None:
            subdir = f"sgs/{frequency}"

        last_date = self.data_manager.get_last_date(filename, subdir)

        if last_date is None:
            # Primeiro download: historico completo
            if verbose:
                print(f"Baixando {name} (historico completo)...")
            df = self.client.get_historical(
                code=code,
                name=name,
                frequency=frequency,
                verbose=verbose
            )
            if not df.empty and save:
                self.data_manager.save(
                    df, filename, subdir,
                    metadata={'sgs_code': code, 'name': name}
                )
        else:
            # Atualizacao incremental
            df = self.client.get_incremental(
                code=code,
                name=name,
                frequency=frequency,
                last_date=last_date,
                verbose=verbose
            )
            if not df.empty and save:
                self.data_manager.append(df, filename, subdir)

        return df

    # =========================================================================
    # NIVEL 2: API Simplificada
    # =========================================================================

    def collect(
        self,
        indicators: list[str] | str = 'all',
        save: bool = True,
        verbose: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Coleta um ou mais indicadores.

        Args:
            indicators: Indicadores a coletar:
                - 'all': todos de SGS_CONFIG
                - lista: ['selic', 'cdi', ...]
                - string: 'selic' (um unico)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            Dict {indicator_key: DataFrame} com dados coletados
        """
        # Normalizar entrada
        if indicators == 'all':
            keys = list(SGS_CONFIG.keys())
        elif isinstance(indicators, str):
            keys = [indicators]
        else:
            keys = list(indicators)

        # Verificar se e primeiro run
        is_first_run = not (self.data_path / 'raw' / 'sgs').exists()

        if verbose:
            print("=" * 70)
            if is_first_run:
                print("PRIMEIRA EXECUCAO - Download de Historico Completo")
            else:
                print("ATUALIZACAO INCREMENTAL")
            print("=" * 70)
            print(f"Indicadores a coletar: {len(keys)}")
            print()

        results = {}
        for key in keys:
            config = get_indicator_config(key)
            subdir = f"sgs/{config['frequency']}"

            df = self.collect_series(
                code=config['code'],
                filename=key,
                name=config['name'],
                frequency=config['frequency'],
                subdir=subdir,
                save=save,
                verbose=verbose,
            )
            results[key] = df

            if verbose:
                print()

        if verbose:
            print("=" * 70)
            print("Coleta concluida!")
            print("=" * 70)

        return results

    # =========================================================================
    # Consolidacao
    # =========================================================================

    def consolidate(
        self,
        subdirs: list[str] | str = None,
        output_prefix: str = None,
        save: bool = True,
        verbose: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Consolida arquivos de um ou mais subdiretorios.

        Args:
            subdirs: Subdiretorios a consolidar:
                - None: usa default_consolidate_subdirs (['sgs/daily', 'sgs/monthly'])
                - lista: ['sgs/daily', 'sgs/monthly']
                - string: 'sgs/daily' (um unico)
            output_prefix: Prefixo para nomes de arquivo (default: sgs_daily_consolidated)
            save: Se True, salva em processed/
            verbose: Se True, imprime progresso

        Returns:
            Dict {subdir: DataFrame} com dados consolidados
        """
        # Normalizar entrada
        if subdirs is None:
            subdirs_list = self.default_consolidate_subdirs
        elif isinstance(subdirs, str):
            subdirs_list = [subdirs]
        else:
            subdirs_list = list(subdirs)

        if verbose:
            print("=" * 70)
            print("CONSOLIDANDO DADOS")
            print("=" * 70)
            print()

        results = {}
        for subdir in subdirs_list:
            # Gerar nome de arquivo (sgs/daily -> sgs_daily_consolidated)
            subdir_safe = subdir.replace('/', '_')
            output_name = f"{output_prefix or subdir_safe}_consolidated" if save else None

            df = self.data_manager.consolidate(
                subdir=subdir,
                output_filename=output_name,
                save=save,
                verbose=verbose,
            )
            results[subdir] = df

            if verbose and not df.empty:
                print(f"  {subdir}: {df.shape[0]:,} registros x {df.shape[1]} colunas")
                if hasattr(df.index, 'min') and hasattr(df.index, 'max'):
                    try:
                        print(f"  Periodo: {df.index.min().date()} a {df.index.max().date()}")
                    except AttributeError:
                        pass
                print()

        if verbose:
            print("Consolidacao concluida!")

        return results
