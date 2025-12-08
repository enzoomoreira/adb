"""
Coletor de expectativas do BCB (Relatorio Focus).

Orquestra a coleta de dados de expectativas com flexibilidade de parametros.
"""

from pathlib import Path
import pandas as pd

from ..base import BaseCollector
from .client import ExpectationsClient
from .indicators import EXPECTATIONS_CONFIG, get_indicator_config


class ExpectationsCollector(BaseCollector):
    """
    Orquestrador de coleta de expectativas do BCB.

    Oferece dois niveis de uso:
    1. collect_endpoint() - Controle total, usuario define tudo
    2. collect() - Usa config predefinida, coleta um ou mais indicadores

    Herda de BaseCollector:
    - save(), read(), list_files() - delegacoes para DataManager
    - get_status() - status dos arquivos salvos
    """

    default_subdir = 'bacen/expectations'
    default_consolidate_subdirs = ['bacen/expectations']

    def __init__(self, data_path: Path):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho base para diretorio data/
        """
        super().__init__(data_path)
        self.client = ExpectationsClient()

    # =========================================================================
    # NIVEL 1: Controle Total
    # =========================================================================

    def collect_endpoint(
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
            self._log_fetch_start(log_name, effective_start, verbose)
            return self.client.query(
                endpoint_key=endpoint,
                indicator=indicator,
                start_date=effective_start,
                end_date=end_date,
                limit=limit,
            )

        if save:
            df, _ = self.data_manager.fetch_and_sync(
                filename=filename,
                subdir=subdir,
                fetch_fn=fetch,
                verbose=False,
            )
        else:
            df = fetch(start_date)

        # Log resultado
        self._log_fetch_result(log_name, len(df), verbose)

        return df

    # =========================================================================
    # NIVEL 2: API Simplificada
    # =========================================================================

    def collect(
        self,
        indicators: list[str] | str = 'all',
        start_date: str = None,
        limit: int = None,
        save: bool = True,
        verbose: bool = True,
    ) -> dict[str, pd.DataFrame]:
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
        if indicators == 'all':
            keys = list(EXPECTATIONS_CONFIG.keys())
        elif isinstance(indicators, str):
            keys = [indicators]
        else:
            keys = list(indicators)

        if verbose:
            is_first_run = self.data_manager.is_first_run(self.default_subdir)
            print("=" * 70)
            if is_first_run:
                print("PRIMEIRA EXECUCAO - Download Completo")
            else:
                print("ATUALIZACAO INCREMENTAL")
            print("=" * 70)
            print(f"Indicadores a coletar: {len(keys)}")
            print()

        results = {}
        for key in keys:
            config = get_indicator_config(key)

            df = self.collect_endpoint(
                endpoint=config['endpoint'],
                filename=key,
                indicator=config['indicator'],
                start_date=start_date,
                limit=limit,
                subdir=self.default_subdir,
                save=save,
                verbose=verbose,
            )
            results[key] = df

            if verbose:
                print()

        if verbose:
            print("=" * 70)
            total = sum(len(df) for df in results.values())
            print(f"Coleta concluida! Total: {total:,} registros")
            print("=" * 70)

        return results

    # =========================================================================
    # Consolidacao
    # =========================================================================

    def consolidate(
        self,
        subdirs: list[str] | str = None,
        output_prefix: str = 'expectations',
        add_source: bool = True,
        save: bool = True,
        verbose: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Consolida arquivos de um ou mais subdiretorios.

        Args:
            subdirs: Subdiretorios a consolidar:
                - None: usa default_consolidate_subdirs (['expectations'])
                - lista: ['expectations']
                - string: 'expectations' (um unico)
            output_prefix: Prefixo para nomes de arquivo (default: 'expectations')
            add_source: Se True, adiciona coluna '_source' com nome do arquivo
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
            print("CONSOLIDANDO EXPECTATIVAS")
            print("=" * 70)
            print()

        results = {}
        for subdir in subdirs_list:
            # Consolidar sem salvar - precisamos processar antes
            df = self.data_manager.consolidate(
                subdir=subdir,
                output_filename=None,
                save=False,
                verbose=verbose,
                add_source=add_source,
            )

            # ---------------------------------------------------------------------
            # Converter coluna 'Data' para DatetimeIndex
            #
            # Por que fazer isso:
            # - Padroniza com o resto do projeto (SGS usa DatetimeIndex)
            # - Facilita fatiamento temporal: df.loc['2025-01']
            #
            # Por que indices duplicados sao aceitaveis:
            # - Cada data tem multiplos registros (projecoes para diferentes anos)
            # - Exemplo: 2025-11-28 tem projecoes para 2025, 2026, 2027, 2028, 2029
            # - Pandas lida bem com isso, permite filtrar por DataReferencia
            #
            # Por que fazer apenas no consolidado (nao no raw):
            # - Arquivos raw preservam estrutura original da API
            # - Consolidado e otimizado para analise
            # ---------------------------------------------------------------------
            if 'Data' in df.columns and not df.empty:
                df = df.set_index('Data').sort_index()
                df.index.name = 'Date'  # Padronizar nome do indice

            # Salvar arquivo processado
            if save and not df.empty:
                output_name = f"{output_prefix}_consolidated"
                output_path = self.data_manager.processed_path / f"{output_name}.parquet"
                self.data_manager.processed_path.mkdir(parents=True, exist_ok=True)
                df.to_parquet(output_path, engine='pyarrow', compression='snappy', index=True)
                if verbose:
                    print(f"  Salvo: {output_path.relative_to(self.data_manager.base_path)}")

            results[subdir] = df

            if verbose and not df.empty:
                print(f"  {subdir}: {len(df):,} registros")
                print()

        if verbose:
            print("Consolidacao concluida!")

        return results
