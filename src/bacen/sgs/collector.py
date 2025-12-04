"""
Coletor de dados SGS do BCB.

Orquestra a coleta de series temporais com flexibilidade de parametros.
"""

from pathlib import Path
import pandas as pd

from .client import SGSClient
from .indicators import INDICATORS, get_by_frequency, get_indicator_config
from data import DataManager


class SGSCollector:
    """
    Orquestrador de coleta de dados SGS.

    Oferece tres niveis de uso:
    1. collect_series() - Controle total, usuario define codigo SGS e filename
    2. collect_indicator() - Usa config predefinida com override opcional
    3. collect_all() - Automacao completa
    """

    def __init__(self, data_path: Path):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho para diretorio data/
        """
        self.data_path = Path(data_path)
        self.client = SGSClient()
        self.data_manager = DataManager(data_path)

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
            subdir = frequency

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
    # NIVEL 2: Config Predefinida
    # =========================================================================

    def collect_indicator(
        self,
        key: str,
        filename: str = None,
        subdir: str = None,
        config: dict = None,
        save: bool = True,
        verbose: bool = True
    ) -> pd.DataFrame:
        """
        Coleta um indicador usando configuracao predefinida.

        Args:
            key: Chave do indicador (ex: 'selic', 'dolar_ptax')
            filename: Nome do arquivo (default: usa key)
            subdir: Subdiretorio (default: usa frequency do indicador)
            config: Configuracao do indicador (default: busca em INDICATORS)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso

        Returns:
            DataFrame com dados coletados
        """
        if config is None:
            config = INDICATORS.get(key)
            if config is None:
                raise ValueError(f"Indicador '{key}' nao encontrado em INDICATORS")

        code = config['code']
        name = config['name']
        frequency = config['frequency']

        return self.collect_series(
            code=code,
            filename=filename or key,
            name=name,
            frequency=frequency,
            subdir=subdir or frequency,
            save=save,
            verbose=verbose,
        )

    # =========================================================================
    # NIVEL 3: Automatico
    # =========================================================================

    def collect_all(
        self,
        indicators: dict = None,
        subdir_daily: str = 'daily',
        subdir_monthly: str = 'monthly',
        save: bool = True,
        verbose: bool = True
    ) -> dict[str, pd.DataFrame]:
        """
        Coleta todos os indicadores (historico ou incremental automatico).

        Args:
            indicators: Dict de indicadores (default: INDICATORS)
            subdir_daily: Subdiretorio para indicadores diarios
            subdir_monthly: Subdiretorio para indicadores mensais
            save: Se True, salva cada indicador em Parquet
            verbose: Se True, imprime progresso

        Returns:
            Dict {indicator_key: DataFrame} com dados coletados
        """
        if indicators is None:
            indicators = INDICATORS

        is_first_run = not (self.data_path / 'raw' / 'daily').exists()

        if verbose:
            print("=" * 70)
            if is_first_run:
                print("PRIMEIRA EXECUCAO - Download de Historico Completo")
            else:
                print("ATUALIZACAO INCREMENTAL")
            print("=" * 70)
            print()

        results = {}
        for key, config in indicators.items():
            subdir = subdir_daily if config['frequency'] == 'daily' else subdir_monthly
            df = self.collect_indicator(
                key=key,
                filename=key,
                subdir=subdir,
                config=config,
                save=save,
                verbose=verbose
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
        files: list[str] = None,
        output_filename: str = None,
        subdir: str = 'daily',
        save: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Consolida multiplos arquivos em um DataFrame.

        Args:
            files: Lista de arquivos (default: todos do subdir)
            output_filename: Nome do arquivo consolidado
            subdir: Subdiretorio dentro de raw/
            save: Se True, salva em processed/
            verbose: Se True, imprime progresso

        Returns:
            DataFrame consolidado
        """
        return self.data_manager.consolidate(
            files=files,
            output_filename=output_filename,
            subdir=subdir,
            save=save,
            verbose=verbose,
        )

    def consolidate_all(
        self,
        output_daily: str = 'daily_consolidated',
        output_monthly: str = 'monthly_consolidated',
        save: bool = True,
        verbose: bool = True
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Consolida e salva dados mensais e diarios.

        Args:
            output_daily: Nome do arquivo consolidado diario
            output_monthly: Nome do arquivo consolidado mensal
            save: Se True, salva arquivos Parquet consolidados
            verbose: Se True, imprime progresso

        Returns:
            Tupla (df_monthly, df_daily) com dados consolidados
        """
        if verbose:
            print("=" * 70)
            print("CONSOLIDANDO DADOS")
            print("=" * 70)
            print()

        df_monthly = self.data_manager.consolidate(
            subdir='monthly',
            output_filename=output_monthly if save else None,
            save=save,
            verbose=verbose,
        )

        df_daily = self.data_manager.consolidate(
            subdir='daily',
            output_filename=output_daily if save else None,
            save=save,
            verbose=verbose,
        )

        if verbose:
            if not df_monthly.empty:
                print(f"Mensal: {df_monthly.shape[0]:,} registros x {df_monthly.shape[1]} indicadores")
                print(f"  Periodo: {df_monthly.index.min().date()} a {df_monthly.index.max().date()}")

            if not df_daily.empty:
                print(f"Diario: {df_daily.shape[0]:,} registros x {df_daily.shape[1]} indicadores")
                print(f"  Periodo: {df_daily.index.min().date()} a {df_daily.index.max().date()}")

            print()
            print("Consolidacao concluida!")

        return df_monthly, df_daily

    # =========================================================================
    # Utilitarios
    # =========================================================================

    def save(
        self,
        df: pd.DataFrame,
        filename: str,
        subdir: str = 'daily',
        **kwargs
    ):
        """Delega para DataManager.save()"""
        return self.data_manager.save(df, filename, subdir, **kwargs)

    def read(
        self,
        filename: str,
        subdir: str = 'daily',
    ) -> pd.DataFrame:
        """Delega para DataManager.read()"""
        return self.data_manager.read(filename, subdir)

    def list_files(
        self,
        subdir: str = 'daily',
    ) -> list[str]:
        """Delega para DataManager.list_files()"""
        return self.data_manager.list_files(subdir)

    def get_status(
        self,
        subdirs: list[str] = None,
    ) -> pd.DataFrame:
        """
        Retorna status de cada indicador (ultima data, registros, etc).

        Args:
            subdirs: Lista de subdiretorios (default: ['daily', 'monthly'])

        Returns:
            DataFrame com status de todos os indicadores
        """
        if subdirs is None:
            subdirs = ['daily', 'monthly']

        status_data = []

        for key, config in INDICATORS.items():
            freq = config['frequency']
            if freq not in subdirs:
                continue

            df = self.data_manager.read(key, freq)

            if df.empty:
                status_data.append({
                    'indicador': key,
                    'nome': config['name'],
                    'frequencia': freq,
                    'primeira_data': None,
                    'ultima_data': None,
                    'registros': 0,
                    'status': 'Sem dados'
                })
            else:
                status_data.append({
                    'indicador': key,
                    'nome': config['name'],
                    'frequencia': freq,
                    'primeira_data': df.index.min().date(),
                    'ultima_data': df.index.max().date(),
                    'registros': len(df),
                    'status': 'OK'
                })

        return pd.DataFrame(status_data)
