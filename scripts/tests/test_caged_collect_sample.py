"""
Script para testar coleta de amostra do CAGED.

Baixa apenas os ultimos 2 meses de CAGEDMOV para validar:
- Coleta incremental funciona
- Salvamento em parquet
- Leitura dos dados salvos

Uso: uv run scripts/test_caged_collect_sample.py
"""

from pathlib import Path
import sys

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mte.caged import CAGEDCollector, CAGEDClient, get_available_periods
import pandas as pd


def main():
    print("=" * 70)
    print("TESTE DE COLETA CAGED (AMOSTRA)")
    print("=" * 70)
    print()

    # Verificar periodos disponiveis
    periods = get_available_periods()
    print(f"Periodos disponiveis: {len(periods)} meses")
    print(f"Primeiro: {periods[0][0]}-{periods[0][1]:02d}")
    print(f"Ultimo: {periods[-1][0]}-{periods[-1][1]:02d}")
    print()

    # Coletar apenas os ultimos 2 meses para teste rapido
    test_periods = periods[-2:]
    print(f"Periodos de teste: {test_periods}")
    print()

    # Inicializar
    data_path = Path(__file__).parent.parent / 'data'
    client = CAGEDClient(timeout=300)
    client.connect()

    dfs = []
    try:
        for year, month in test_periods:
            print(f"Baixando CAGEDMOV {year}-{month:02d}...")
            df = client.get_data('CAGEDMOV', year, month, verbose=True)
            if not df.empty:
                dfs.append(df)
    finally:
        client.disconnect()

    if not dfs:
        print("Nenhum dado baixado!")
        return

    # Concatenar
    full_df = pd.concat(dfs, ignore_index=True)
    print()
    print(f"Total de registros: {len(full_df):,}")
    print(f"Memoria: {full_df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

    # Salvar usando DataManager
    print()
    print("-" * 70)
    print("SALVANDO VIA DATAMANAGER")
    print("-" * 70)

    from data import DataManager
    dm = DataManager(data_path)

    # Salvar como teste
    dm.save(full_df, 'cagedmov_test', 'mte/caged', verbose=True)

    # Verificar arquivo
    print()
    print("-" * 70)
    print("VERIFICANDO ARQUIVO SALVO")
    print("-" * 70)

    df_loaded = dm.read('cagedmov_test', 'mte/caged')
    print(f"Registros carregados: {len(df_loaded):,}")
    print(f"Colunas: {len(df_loaded.columns)}")

    # Verificar periodos
    print()
    print("Periodos no arquivo:")
    for (ano, mes), count in df_loaded.groupby(['ano_ref', 'mes_ref']).size().items():
        print(f"  {ano}-{mes:02d}: {count:,} registros")

    # Agora testar o collector completo
    print()
    print("-" * 70)
    print("TESTANDO COLLECTOR")
    print("-" * 70)

    collector = CAGEDCollector(data_path)

    # Limpar arquivo de teste
    test_file = data_path / 'raw' / 'mte' / 'caged' / 'cagedmov_test.parquet'
    if test_file.exists():
        test_file.unlink()
        print("Arquivo de teste removido")

    # Status inicial
    print()
    print("Status inicial:")
    status = collector.get_status()
    if status.empty:
        print("  Nenhum arquivo")
    else:
        print(status.to_string())

    print()
    print("=" * 70)
    print("TESTE CONCLUIDO!")
    print("=" * 70)
    print()
    print("Para coletar o historico completo, execute:")
    print("  uv run scripts/collect_caged_full.py")


if __name__ == '__main__':
    main()
