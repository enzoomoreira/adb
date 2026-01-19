"""
Coletor de dados do Novo CAGED.

Orquestra a coleta de microdados do CAGED via FTP,
com suporte a atualizacoes incrementais e download paralelo.
"""

import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import py7zr
import duckdb
import pandas as pd
from tqdm.auto import tqdm

from core.collectors import BaseCollector
from core.utils import get_indicator_config
from .client import CAGEDClient
from .indicators import CAGED_CONFIG, get_available_periods


class CAGEDCollector(BaseCollector):
    """
    Orquestra coleta de dados do Novo CAGED.

    API publica:
    - collect() - Coleta microdados do CAGED via FTP
    - get_status() - Status dos dados locais (override - usa periodos)

    Para leitura e queries SQL nos dados coletados, use QueryEngine:
        from core.data import QueryEngine
        qe = QueryEngine('data/')
        df = qe.sql("SELECT * FROM '{raw}/mte/caged/cagedmov_*.parquet'")

    Herda de BaseCollector para padronizacao de logging.
    """

    default_subdir = 'mte/caged'

    def __init__(self, data_path: Path = None):
        """
        Inicializa o coletor.

        Args:
            data_path: Caminho para diretorio data/ (opcional, usa DATA_PATH se None)
        """
        super().__init__(data_path)
        self.client = CAGEDClient()
        self._db_lock = Lock()

    def _get_last_period(self, filename: str, subdir: str) -> tuple[int, int] | None:
        """
        Retorna (ano, mes) do ultimo periodo salvo.
        Verifica arquivos mensais no diretório.
        """
        files = self.data_manager.list_files(subdir)
        prefix = f"{filename}_"
        candidates = [f for f in files if f.startswith(prefix)]

        if candidates:
            candidates.sort()
            last_file = candidates[-1]
            try:
                _, date_part = last_file.rsplit("_", 1)
                year, month = map(int, date_part.split("-"))
                return (year, month)
            except (ValueError, IndexError):
                pass

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

        return [p for p in all_periods if p > last]

    def _fetch_single_period(
        self,
        indicator_key: str,
        year: int,
        month: int,
    ) -> tuple[int, int, int, str | None]:
        """
        Baixa, extrai e converte um unico periodo.
        
        Usa DuckDB para converter CSV -> Parquet de forma eficiente.

        Returns:
            Tupla (year, month, rows, error_msg)
        """
        config = get_indicator_config(CAGED_CONFIG, indicator_key)
        subdir = "mte/caged"
        
        # Criar diretório temporário para este período
        temp_dir = Path(tempfile.mkdtemp(prefix=f"caged_{year}{month:02d}_"))
        
        client = CAGEDClient()
        try:
            client.connect()
            
            # 1. Download 7z para temp
            archive_path = temp_dir / f"{config['prefix']}{year}{month:02d}.7z"
            client.download_to_file(config["prefix"], year, month, archive_path)
            
            # 2. Extrair 7z
            with py7zr.SevenZipFile(archive_path, 'r') as archive:
                archive.extractall(path=temp_dir)
            
            # 3. Encontrar CSV extraído
            csv_files = list(temp_dir.glob("*.txt")) + list(temp_dir.glob("*.csv"))
            if not csv_files:
                return (year, month, 0, "Nenhum CSV encontrado no 7z")
            
            csv_path = next((f for f in csv_files if config['prefix'] in f.name.upper()), csv_files[0])
            
            # 4. Converter para Parquet usando DuckDB (ETL otimizado)
            output_filename = f"{indicator_key}_{year}-{month:02d}.parquet"
            output_path = self.data_manager.raw_path / subdir / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # DuckDB consome muitos recursos, melhor serializar a conversao
            # enquanto mantemos downloads em paralelo (via worker threads)
            # Para isso usamos um lock global ou de classe, mas aqui usaremos connection isolada
            
            query = f"""
                COPY (
                    SELECT * 
                    FROM read_csv('{str(csv_path)}', delim=';', header=True, encoding='utf-8', ignore_errors=True)
                ) TO '{str(output_path)}' (FORMAT 'parquet', COMPRESSION 'snappy')
            """
            
            # Serializar apenas a etapa de CPU heavy do DuckDB para evitar travamento
            with self._db_lock:
                # Desabilitar barra de progresso do DuckDB para nao poluir notebook
                duckdb.sql("SET enable_progress_bar = false;")
                duckdb.sql(query)
                row_count = duckdb.sql(f"SELECT COUNT(*) FROM '{str(output_path)}'").fetchone()[0]
            
            return (year, month, row_count, None)

        except Exception as e:
            return (year, month, 0, f"Erro: {str(e)}")

        finally:
            # Garantir limpeza
            try:
                if 'client' in locals():
                    client.disconnect()
            except:
                pass
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    def collect(
        self,
        indicators: list[str] | str = "all",
        save: bool = True,
        verbose: bool = True,
        max_workers: int = 4,
    ) -> dict[str, int]:
        """
        Coleta dados do CAGED (Raw Layer).

        Args:
            indicators: 'all', ou lista de chaves
            save: Se True, salva os arquivos (sempre True, compatibilidade)
            verbose: Se True, imprime logs
            max_workers: Numero de threads para download paralelo
        """
        keys = self._normalize_indicators_list(indicators, CAGED_CONFIG)
        subdir = "mte/caged"
        
        # Log inicial padronizado
        self._log_collect_start(
            title="CAGED - Ministerio do Trabalho e Emprego",
            num_indicators=len(keys),
            subdir=subdir,
            check_first_run=True,
            verbose=verbose
        )

        results = {}

        for key in keys:
            config = get_indicator_config(CAGED_CONFIG, key)
            missing = self._get_missing_periods(key, subdir, config["start_year"])

            if not missing:
                if verbose:
                    print(f"  {config['name']}: Dados atualizados")
                results[key] = 0
                continue

            if verbose:
                print(f"  {config['name']}: Baixando {len(missing)} meses...")

            total_rows = 0
            errors = []
            
            # Coleta Paralela com ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submeter todas as tarefas
                future_to_period = {
                    executor.submit(self._fetch_single_period, key, year, month): (year, month)
                    for year, month in missing
                }
                
                # Barra de progresso
                pbar = tqdm(
                    as_completed(future_to_period),
                    total=len(missing),
                    desc=f"  {config['prefix']}",
                    unit="mês",
                    disable=not verbose,
                    leave=False
                )
                
                for future in pbar:
                    year, month, rows, error = future.result()
                    
                    if error:
                        errors.append(f"{year}-{month:02d}: {error}")
                    else:
                        total_rows += rows
                
                pbar.close()

            if verbose and errors:
                print(f"    Erros ({len(errors)}): {', '.join(errors[:3])}...")

            results[key] = total_rows

        self._log_collect_end(results, verbose=verbose)
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
                    "ultimo_periodo": f"{last[0]}-{last[1]:02d}" if last else "Nao iniciado",
                    "status": "Ok" if last else "Pendente",
                }
            )

        return pd.DataFrame(status)
