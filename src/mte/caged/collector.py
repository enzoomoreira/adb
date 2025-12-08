"""
Coletor de dados do Novo CAGED.

Orquestra a coleta de microdados do CAGED via FTP,
com suporte a atualizacoes incrementais.
"""

from pathlib import Path

import pandas as pd

from data import DataManager
from .client import CAGEDClient
from .indicators import CAGED_CONFIG, get_indicator_config, get_available_periods


class CAGEDCollector:
    """Orquestra coleta de dados do Novo CAGED."""

    def __init__(self, data_path: Path):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho para diretorio data/
        """
        self.data_path = Path(data_path)
        self.data_manager = DataManager(data_path)
        self.client = CAGEDClient()

    def _get_last_period(self, filename: str, subdir: str) -> tuple[int, int] | None:
        """
        Retorna (ano, mes) do ultimo periodo salvo.

        Args:
            filename: Nome do arquivo
            subdir: Subdiretorio em raw/

        Returns:
            Tupla (ano, mes) ou None se arquivo nao existe
        """
        df = self.data_manager.read(filename, subdir)
        if df.empty:
            return None

        if 'ano_ref' in df.columns and 'mes_ref' in df.columns:
            last_row = df.iloc[-1]
            return (int(last_row['ano_ref']), int(last_row['mes_ref']))

        return None

    def _get_missing_periods(
        self,
        filename: str,
        subdir: str,
        start_year: int,
    ) -> list[tuple[int, int]]:
        """
        Retorna periodos que faltam baixar.

        Args:
            filename: Nome do arquivo
            subdir: Subdiretorio em raw/
            start_year: Ano inicial

        Returns:
            Lista de (ano, mes) faltantes
        """
        all_periods = get_available_periods(start_year)
        last = self._get_last_period(filename, subdir)

        if last is None:
            return all_periods  # Primeira execucao

        # Filtra periodos apos o ultimo salvo
        missing = []
        for year, month in all_periods:
            if (year, month) > last:
                missing.append((year, month))
        return missing

    def collect(
        self,
        indicators: list[str] | str = 'all',
        save: bool = True,
        verbose: bool = True,
    ) -> dict[str, int]:
        """
        Coleta dados do CAGED com salvamento incremental.

        - Primeira execucao: baixa historico completo (2020+)
        - Execucoes seguintes: apenas meses novos (incremental)
        - Salva cada mes imediatamente (baixo uso de memoria)

        Args:
            indicators: 'all', 'cagedmov', ou ['cagedmov', 'cagedfor']
            save: Salvar em raw/mte/caged/
            verbose: Imprimir progresso

        Returns:
            Dict {indicator: total_registros_novos}
        """
        # Normaliza input
        if indicators == 'all':
            keys = list(CAGED_CONFIG.keys())
        elif isinstance(indicators, str):
            keys = [indicators]
        else:
            keys = list(indicators)

        subdir = 'mte/caged'

        # Verificar se e primeiro run
        is_first_run = self.data_manager.is_first_run(subdir)

        if verbose:
            print("=" * 70)
            print("CAGED - Ministerio do Trabalho e Emprego")
            if is_first_run:
                print("PRIMEIRA EXECUCAO - Download de Historico Completo")
            else:
                print("ATUALIZACAO INCREMENTAL")
            print("=" * 70)
            print(f"Indicadores a coletar: {len(keys)}")
            print()

        self.client.connect()
        results = {}

        try:
            for key in keys:
                config = get_indicator_config(key)
                prefix = config['prefix']
                start_year = config['start_year']

                missing = self._get_missing_periods(key, subdir, start_year)

                if verbose:
                    if not missing:
                        print(f"\n{config['name']}: Dados atualizados")
                        results[key] = 0
                        continue
                    elif self._get_last_period(key, subdir) is None:
                        print(f"\n{config['name']}: Download completo ({len(missing)} meses)")
                    else:
                        print(f"\n{config['name']}: Atualizacao ({len(missing)} meses novos)")

                total_rows = 0
                for year, month in missing:
                    df = self.client.get_data(prefix, year, month, verbose=verbose)

                    if not df.empty:
                        if save:
                            # dedup=False: CAGED sao microdados, cada linha e um registro unico
                            # Nao podemos remover "duplicatas" por indice como em series temporais
                            self.data_manager.append(df, key, subdir, dedup=False, verbose=False)
                        total_rows += len(df)
                    # df sai de escopo aqui, memoria liberada

                if verbose and total_rows > 0:
                    print(f"  Total: {total_rows:,} registros salvos")

                results[key] = total_rows

        finally:
            self.client.disconnect()

        if verbose:
            print("\n" + "=" * 70)
            print("Coleta concluida!")
            print("=" * 70)

        return results

    def read(self, indicator: str = 'cagedmov') -> pd.DataFrame:
        """
        Le dados salvos de um indicador.

        Args:
            indicator: Nome do indicador (cagedmov, cagedfor, cagedexc)

        Returns:
            DataFrame com todos os dados salvos
        """
        return self.data_manager.read(indicator, 'mte/caged')

    def get_status(self) -> pd.DataFrame:
        """
        Retorna status dos arquivos salvos.

        Returns:
            DataFrame com arquivo, registros, ultimo_periodo
        """
        subdir = 'mte/caged'
        files = self.data_manager.list_files(subdir)

        if not files:
            return pd.DataFrame()

        status = []
        for filename in files:
            df = self.data_manager.read(filename, subdir)
            last = self._get_last_period(filename, subdir)

            status.append({
                'arquivo': filename,
                'registros': len(df),
                'ultimo_periodo': f"{last[0]}-{last[1]:02d}" if last else None,
            })

        return pd.DataFrame(status)

    def consolidate(
        self,
        indicators: list[str] | str = 'all',
        save: bool = True,
        verbose: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Consolida dados do CAGED em processed/.

        Os dados raw ja estao consolidados (um arquivo por indicador).
        Este metodo copia para processed/ com eventuais transformacoes.

        Args:
            indicators: 'all', 'cagedmov', ou lista
            save: Salvar em processed/
            verbose: Imprimir progresso

        Returns:
            Dict {indicator: DataFrame}
        """
        if indicators == 'all':
            keys = list(CAGED_CONFIG.keys())
        elif isinstance(indicators, str):
            keys = [indicators]
        else:
            keys = list(indicators)

        if verbose:
            print("=" * 70)
            print("CONSOLIDANDO DADOS CAGED")
            print("=" * 70)
            print()

        results = {}
        for key in keys:
            df = self.read(key)

            if df.empty:
                if verbose:
                    print(f"{key}: Sem dados")
                continue

            if save:
                output_path = self.data_manager.processed_path / f"caged_{key}.parquet"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(output_path, engine='pyarrow', compression='snappy')

                if verbose:
                    print(f"{key}: {len(df):,} registros -> {output_path.name}")

            results[key] = df

        if verbose:
            print()
            print("Consolidacao concluida!")

        return results
