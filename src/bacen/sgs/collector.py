"""
Coletor de dados SGS do BCB.

Orquestra a coleta de series temporais com flexibilidade de parametros.
"""

from pathlib import Path
import pandas as pd

from core.collectors import BaseCollector
from core.indicators import get_indicator_config
from .client import SGSClient
from .indicators import SGS_CONFIG


class SGSCollector(BaseCollector):
    """
    Orquestrador de coleta de dados SGS.

    API publica:
    - collect() - Coleta um ou mais indicadores usando config predefinida
    - consolidate() - Consolida arquivos em DataFrame unico
    - get_status() - Status dos arquivos salvos

    Herda de BaseCollector para logging padronizado e get_status().
    """

    default_subdir = 'bacen/sgs/daily'
    default_consolidate_subdirs = ['bacen/sgs/daily', 'bacen/sgs/monthly']

    def __init__(self, data_path: Path):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho para diretorio data/
        """
        super().__init__(data_path)
        self.client = SGSClient()

    # =========================================================================
    # Metodo interno de coleta
    # =========================================================================

    def _collect_series(
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

        Suporta atualizacao incremental: se ja existem dados salvos,
        busca apenas registros novos desde a ultima data.

        Args:
            code: Codigo SGS do indicador
            filename: Nome do arquivo para salvar (sem extensao)
            name: Nome da serie (default: usa filename)
            frequency: 'daily' ou 'monthly'
            subdir: Subdiretorio dentro de raw/ (default: sgs/{frequency})
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            DataFrame com dados coletados
        """
        if name is None:
            name = filename
        if subdir is None:
            subdir = f"bacen/sgs/{frequency}"

        def fetch(start_date: str | None) -> pd.DataFrame:
            return self.client.get_data(
                code=code,
                name=name,
                frequency=frequency,
                start_date=start_date,
                verbose=False,
            )

        return self._collect_with_sync(
            fetch_fn=fetch,
            filename=filename,
            name=name,
            subdir=subdir,
            frequency=frequency,
            save=save,
            verbose=verbose,
        )

    # =========================================================================
    # API Publica
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
        keys = self._normalize_indicators_list(indicators, SGS_CONFIG)

        self._log_collect_start(
            title="BACEN - Sistema Gerenciador de Series",
            num_indicators=len(keys),
            subdir='bacen/sgs/daily',
            check_first_run=True,
            verbose=verbose,
        )

        results = {}
        for key in keys:
            config = get_indicator_config(SGS_CONFIG, key)
            subdir = f"bacen/sgs/{config['frequency']}"

            df = self._collect_series(
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

        self._log_collect_end(verbose=verbose)

        return results

    # =========================================================================
    # Consolidacao
    # =========================================================================

    @staticmethod
    def _annualize_cdi(daily_rate: pd.Series) -> pd.Series:
        """
        Calcula taxa anualizada a partir da taxa diaria do CDI.

        Formula: ((1 + taxa_diaria/100) ** 252 - 1) * 100

        O CDI vem em percentual diario (ex: 0.055 = 0.055% ao dia).
        Resultado em percentual anual (ex: 14.9 = 14.9% ao ano).
        """
        return ((1 + daily_rate / 100) ** 252 - 1) * 100

    def consolidate(
        self,
        subdirs: list[str] | str = None,
        output_prefix: str = None,
        save: bool = True,
        verbose: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Consolida arquivos de um ou mais subdiretorios.

        Para sgs/daily, adiciona coluna 'cdi_anualizado' com o CDI
        convertido para taxa anual (comparavel com SELIC).

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
        subdirs_list = self._normalize_subdirs_list(subdirs)

        self._log_consolidate_start(verbose=verbose)

        results = {}
        for subdir in subdirs_list:
            # Gerar nome de arquivo (sgs/daily -> sgs_daily_consolidated)
            subdir_safe = subdir.replace('/', '_')
            output_name = f"{output_prefix or subdir_safe}_consolidated" if save else None

            # Consolidar sem salvar primeiro (para aplicar transformacoes)
            df = self.data_manager.consolidate(
                subdir=subdir,
                output_filename=None,
                save=False,
                verbose=verbose,
            )

            # Adicionar cdi_anualizado para dados diarios
            if subdir == 'bacen/sgs/daily' and 'cdi' in df.columns:
                df['cdi_anualizado'] = self._annualize_cdi(df['cdi'])
                if verbose:
                    print("  + Adicionada coluna 'cdi_anualizado'")

            # Salvar se solicitado
            if save and output_name:
                self._save_parquet_to_processed(df, output_name, verbose=verbose)

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
