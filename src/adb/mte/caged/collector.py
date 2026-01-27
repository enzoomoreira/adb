"""
Coletor de dados do Novo CAGED.

Orquestra a coleta de microdados do CAGED via FTP,
com suporte a atualizacoes incrementais e download paralelo.
"""

import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import py7zr
import duckdb
import pandas as pd
from tqdm.auto import tqdm

from adb.core.collectors import BaseCollector
from adb.core.utils import get_indicator_config
from .client import CAGEDClient
from .indicators import CAGED_CONFIG, get_available_periods


class CAGEDCollector(BaseCollector):
    """
    Orquestra coleta de dados do Novo CAGED.

    API publica:
    - collect() - Coleta microdados do CAGED via FTP
    - get_status() - Status dos dados locais (override - usa periodos)

    Para leitura e queries SQL nos dados coletados, use QueryEngine:
        from adb.core.data import QueryEngine
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

    # =========================================================================
    # Metodos internos (Helpers)
    # =========================================================================

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
            
            # 4. Converter para Parquet usando DuckDB
            output_filename = f"{indicator_key}_{year}-{month:02d}.parquet"
            output_path = self.data_manager.raw_path / subdir / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Cada thread usa sua propria connection isolada para paralelismo real
            # DuckDB e thread-safe quando connections sao independentes
            # Como cada thread escreve para arquivo diferente, nao ha conflito
            
            query = f"""
                COPY (
                    SELECT
                        * EXCLUDE (salário, horascontratuais, valorsaláriofixo),
                        TRY_CAST(REPLACE(TRY_CAST(salário AS VARCHAR), ',', '.') AS DOUBLE) as salario,
                        TRY_CAST(REPLACE(TRY_CAST(horascontratuais AS VARCHAR), ',', '.') AS DOUBLE) as horascontratuais,
                        TRY_CAST(REPLACE(TRY_CAST(valorsaláriofixo AS VARCHAR), ',', '.') AS DOUBLE) as valorsalariofixo
                    FROM read_csv('{str(csv_path)}', delim=';', header=True, encoding='utf-8', ignore_errors=True)
                ) TO '{str(output_path)}' (FORMAT 'parquet', COMPRESSION 'snappy')
            """
            
            conn = duckdb.connect()  # Connection isolada por thread
            try:
                conn.execute("SET enable_progress_bar = false")
                conn.execute(query)
                row_count = conn.execute(f"SELECT COUNT(*) FROM '{str(output_path)}'").fetchone()[0]
            finally:
                conn.close()
            
            return (year, month, row_count, None)

        except Exception as e:
            # Extrair mensagem limpa do erro (sem traceback longo)
            error_msg = str(e).split('\n')[0][:80]
            return (year, month, 0, error_msg)

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

    # =========================================================================
    # API Publica
    # =========================================================================

    def collect(
        self,
        indicators: list[str] | str = "all",
        save: bool = True,
        verbose: bool = True,
        max_workers: int = 4,
    ) -> None:
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

            if errors:
                self.logger.warning(f"  {len(errors)} periodo(s) falharam: {', '.join(errors[:3])}")

            results[key] = total_rows

        self._log_collect_end(verbose=verbose)

    def get_status(self) -> pd.DataFrame:
        """
        Retorna status dos arquivos salvos por indicador.

        Agrega metadados de todos os arquivos mensais de cada indicador
        para retornar no formato padrao (arquivo, subdir, registros, colunas,
        primeira_data, ultima_data, status).
        """
        subdir = "mte/caged"
        status_data = []

        for key in CAGED_CONFIG.keys():
            # Glob para pegar todos os arquivos do indicador
            pattern = f"{key}_*.parquet"
            glob_path = self.data_manager.raw_path / subdir / pattern

            files = list((self.data_manager.raw_path / subdir).glob(pattern))

            if not files:
                status_data.append({
                    'arquivo': key,
                    'subdir': subdir,
                    'registros': 0,
                    'colunas': 0,
                    'primeira_data': None,
                    'ultima_data': None,
                    'status': 'Pendente',
                })
                continue

            try:
                # Usa DuckDB para agregar metadados de todos os arquivos
                sql = f"""
                    SELECT
                        COUNT(*) as total,
                        MIN(competênciamov) as min_date,
                        MAX(competênciamov) as max_date
                    FROM '{glob_path}'
                """
                res = duckdb.sql(sql).fetchone()
                total, min_d, max_d = res

                # Pega numero de colunas do primeiro arquivo
                schema = duckdb.sql(f"DESCRIBE SELECT * FROM '{files[0]}' LIMIT 0").df()
                n_cols = len(schema)

                # Converte competenciamov (YYYYMM int) para datetime
                first_date = pd.to_datetime(str(min_d), format='%Y%m') if min_d else None
                last_date = pd.to_datetime(str(max_d), format='%Y%m') if max_d else None

                status_data.append({
                    'arquivo': key,
                    'subdir': subdir,
                    'registros': total,
                    'colunas': n_cols,
                    'primeira_data': first_date,
                    'ultima_data': last_date,
                    'status': 'OK',
                })
            except Exception as e:
                status_data.append({
                    'arquivo': key,
                    'subdir': subdir,
                    'registros': 0,
                    'colunas': 0,
                    'primeira_data': None,
                    'ultima_data': None,
                    'status': f'Erro: {str(e)[:50]}',
                })

        return pd.DataFrame(status_data)
