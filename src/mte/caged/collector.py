"""
Coletor de dados do Novo CAGED.

Orquestra a coleta de microdados do CAGED via FTP,
com suporte a atualizacoes incrementais.
"""

from pathlib import Path

import pandas as pd

from core.collectors import BaseCollector
from core.indicators import get_indicator_config
from core.parallel import ParallelFetcher
from .client import CAGEDClient
from .indicators import CAGED_CONFIG, get_available_periods


class CAGEDCollector(BaseCollector):
    """
    Orquestra coleta de dados do Novo CAGED.

    API publica:
    - collect() - Coleta microdados do CAGED via FTP
    - consolidate() - Consolida arquivos mensais (via DuckDB)
    - get_status() - Status dos dados locais (override - usa periodos)

    Para leitura e queries SQL nos dados coletados, use QueryEngine:
        from core.data import QueryEngine
        qe = QueryEngine('data/')
        df = qe.sql("SELECT * FROM '{raw}/mte/caged/cagedmov_*.parquet'")

    Herda de BaseCollector para padronizacao de logging.
    """

    default_subdir = 'mte/caged'
    default_consolidate_subdirs = ['mte/caged']

    def __init__(self, data_path: Path):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho para diretorio data/
        """
        super().__init__(data_path)
        self.client = CAGEDClient()

    def _get_last_period(self, filename: str, subdir: str) -> tuple[int, int] | None:
        """
        Retorna (ano, mes) do ultimo periodo salvo.
        Verifica tanto arquivos mensais quanto o arquivo legado.
        """
        # 1. Verificar arquivos particionados (ex: cagedmov_2024-01.parquet)
        files = self.data_manager.list_files(subdir)
        prefix = f"{filename}_"
        candidates = [f for f in files if f.startswith(prefix)]

        if candidates:
            candidates.sort()
            last_file = candidates[-1]
            try:
                # Extrai data do nome: cagedmov_2024-01 -> 2024, 1
                _, date_part = last_file.rsplit("_", 1)
                year, month = map(int, date_part.split("-"))
                return (year, month)
            except (ValueError, IndexError):
                pass

        # 2. Fallback: Verificar arquivo unico legado (ex: cagedmov.parquet)
        if filename in files:
            df = self.data_manager.read(filename, subdir)
            if not df.empty and "ano_ref" in df.columns and "mes_ref" in df.columns:
                last_row = df.iloc[-1]
                return (int(last_row["ano_ref"]), int(last_row["mes_ref"]))

        return None

    def _get_missing_periods(
        self,
        filename: str,
        subdir: str,
        start_year: int,
    ) -> list[tuple[int, int]]:
        """Retorna periodos que faltam baixar."""
        all_periods = get_available_periods(start_year)
        last = self._get_last_period(filename, subdir)

        if last is None:
            return all_periods

        missing = []
        for year, month in all_periods:
            if (year, month) > last:
                missing.append((year, month))
        return missing

    def _fetch_single_period(
        self, indicator_key: str, year: int, month: int, save: bool, verbose: bool
    ) -> int:
        """
        Baixa e salva um unico periodo (thread-safe).

        Cria uma nova instancia de CAGEDClient para garantir isolamento
        de conexao FTP em threads separadas.
        """
        # Recupera config aqui (dentro da thread)
        config = get_indicator_config(CAGED_CONFIG, indicator_key)

        # Cliente dedicado para esta thread/task
        client = CAGEDClient()
        try:
            client.connect()
            df = client.get_data(config["prefix"], year, month, verbose=verbose)

            rows = 0
            if not df.empty:
                if save:
                    file_name = f"{indicator_key}_{year}-{month:02d}"
                    subdir = "mte/caged"
                    self.data_manager.save(df, file_name, subdir, verbose=False)
                rows = len(df)

            return rows
        finally:
            client.disconnect()

    def collect(
        self,
        indicators: list[str] | str = "all",
        save: bool = True,
        verbose: bool = True,
        parallel: bool = True,
        max_workers: int = 4,
    ) -> dict[str, int]:
        """
        Coleta dados do CAGED (Raw Layer).
        Salva arquivos mensais individuais para evitar MemoryError.

        Args:
            indicators: 'all', ou lista de chaves
            save: Se True, salva os arquivos
            verbose: Se True, imprime logs
            parallel: Se True, baixa meses em paralelo
            max_workers: Numero de threads (se parallel=True)
        """
        if indicators == "all":
            keys = list(CAGED_CONFIG.keys())
        elif isinstance(indicators, str):
            keys = [indicators]
        else:
            keys = list(indicators)

        subdir = "mte/caged"

        if verbose:
            print("=" * 70)
            print("CAGED - Ministerio do Trabalho e Emprego")
            print("Estrategia: Arquivos Mensais (Raw) -> Consolidados (Processed)")
            print(
                f"Modo: {'Paralelo' if parallel else 'Sequencial'} (workers={max_workers})"
            )
            print("=" * 70)

        # Se nao for paralelo, usa o client compartilhado (mantendo comportamento original)
        if not parallel:
            self.client.connect()

        results = {}

        try:
            for key in keys:
                config = get_indicator_config(CAGED_CONFIG, key)

                missing = self._get_missing_periods(key, subdir, config["start_year"])

                if verbose:
                    if not missing:
                        print(f"\n{config['name']}: Dados atualizados")
                        results[key] = 0
                        continue
                    else:
                        print(f"\n{config['name']}: Baixando {len(missing)} meses...")

                total_rows = 0

                if parallel:
                    # Prepara tasks (tuplas devem ser hashable para o ParallelFetcher)
                    # Passamos 'key' (str) em vez de 'config' (dict)
                    tasks = [(key, y, m, save, verbose) for y, m in missing]

                    # Funcao adapter para o ParallelFetcher
                    def fetch_adapter(args):
                        return self._fetch_single_period(*args)

                    fetcher = ParallelFetcher(max_workers=max_workers)
                    # O map/fetch_all retorna dict {item: result}
                    # Aqui nossos itens sao tuplas de args
                    batch_results = fetcher.fetch_all(tasks, fetch_adapter)

                    # Soma linhas baixadas com sucesso (ignorando Nones)
                    total_rows = sum(r for r in batch_results.values() if r is not None)

                else:
                    # Modo sequencial (original)
                    for year, month in missing:
                        df = self.client.get_data(
                            config["prefix"], year, month, verbose=verbose
                        )

                        if not df.empty:
                            if save:
                                file_name = f"{key}_{year}-{month:02d}"
                                self.data_manager.save(
                                    df, file_name, subdir, verbose=False
                                )
                            total_rows += len(df)

                results[key] = total_rows
                if verbose and total_rows > 0:
                    print(f"  Total coletado: {total_rows:,} registros")

        finally:
            if not parallel:
                self.client.disconnect()

        return results

    def get_status(self) -> pd.DataFrame:
        """Status dos dados locais."""
        subdir = "mte/caged"
        status = []

        for key in CAGED_CONFIG.keys():
            last = self._get_last_period(key, subdir)
            status.append(
                {
                    "indicador": key,
                    "ultimo_periodo": f"{last[0]}-{last[1]:02d}"
                    if last
                    else "Nao iniciado",
                    "status": "Ok" if last else "Pendente",
                }
            )

        return pd.DataFrame(status)
