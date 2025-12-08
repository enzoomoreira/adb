import sys
import time
import threading
from unittest.mock import MagicMock, patch
from pathlib import Path

# Adiciona raiz do projeto ao path
# Assumindo que o script esta em scripts/tests/verify_parallel.py
# A raiz do projeto esta em ../../
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.mte.caged.collector import CAGEDCollector


def mock_get_data(prefix, year, month, verbose=False):
    """Simula download demorado"""
    t_name = threading.current_thread().name
    print(f"[{t_name}] Simulando download: {year}-{month}")
    time.sleep(0.5)  # Simula delay
    return MagicMock(empty=False, __len__=lambda x: 100)  # Retorna dataframe mockado


def verify_parallel_execution():
    print("Iniciando Verificacao de Paralelismo...")

    # Mockando o Client para nao bater no FTP real
    with patch("src.mte.caged.collector.CAGEDClient") as MockClient:
        instance = MockClient.return_value
        instance.get_data.side_effect = mock_get_data

        collector = CAGEDCollector(data_path="test_data")

        # Mockando get_missing_periods para forcar 'download' de varios meses
        # Retorna 5 meses para teste
        collector._get_missing_periods = MagicMock(
            return_value=[(2024, 1), (2024, 2), (2024, 3), (2024, 4), (2024, 5)]
        )

        # Mockando DataManager.save para nao gravar disco
        collector.data_manager.save = MagicMock()

        start_time = time.time()

        # Executa com 5 workers
        print("\n--- Iniciando Coleta Paralela (5 tasks, 5 workers) ---")
        collector.collect(
            indicators="cagedmov", parallel=True, max_workers=5, verbose=True
        )

        duration = time.time() - start_time
        print(f"\nDuracao Total: {duration:.2f}s")

        # Se fosse sequencial, levaria 0.5s * 5 = 2.5s
        # Se paralelo funcionar, deve levar pouco mais que 0.5s (todos ao mesmo tempo)
        if duration < 1.0:
            print("\nSUCESSO: Execucao paralela confirmada! (Tempo < 1.0s)")
        else:
            print("\nALERTA: Tempo alto, verificar se houve paralelismo real.")


if __name__ == "__main__":
    verify_parallel_execution()
