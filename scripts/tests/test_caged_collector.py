"""
Script para testar o CAGEDCollector.

Testa:
- Listagem de indicadores
- Coleta de um mes (para teste rapido)
- Salvamento em parquet
- Leitura dos dados salvos
- Status

Uso: uv run scripts/test_caged_collector.py
"""

from pathlib import Path
import sys

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mte.caged import (
    CAGEDCollector,
    CAGED_CONFIG,
    list_indicators,
    get_indicator_config,
    get_available_periods,
)


def main():
    print("=" * 70)
    print("TESTE DO MODULO CAGED COLLECTOR")
    print("=" * 70)
    print()

    # Mostrar indicadores disponiveis
    print("1. Indicadores disponiveis:")
    for key in list_indicators():
        config = get_indicator_config(key)
        print(f"   - {key}: {config['name']}")
        print(f"     {config['description']}")
    print()

    # Mostrar periodos disponiveis
    print("2. Periodos disponiveis:")
    periods = get_available_periods()
    print(f"   Total: {len(periods)} meses")
    print(f"   De: {periods[0][0]}-{periods[0][1]:02d}")
    print(f"   Ate: {periods[-1][0]}-{periods[-1][1]:02d}")
    print()

    # Inicializar collector
    data_path = Path(__file__).parent.parent / 'data'
    collector = CAGEDCollector(data_path)
    print(f"3. Data path: {data_path}")
    print()

    # Verificar status inicial
    print("4. Status inicial:")
    status = collector.get_status()
    if status.empty:
        print("   Nenhum arquivo salvo ainda")
    else:
        print(status.to_string())
    print()

    # Teste: Coletar apenas cagedmov
    # NOTA: Para teste completo, isso baixaria todos os meses desde 2020
    # Para um teste rapido, podemos limitar ou apenas verificar a estrutura
    print("-" * 70)
    print("5. Teste de coleta (cagedmov)")
    print("-" * 70)
    print()
    print("ATENCAO: A primeira execucao baixa ~60 meses de dados.")
    print("Isso pode levar varios minutos e usar bastante memoria.")
    print()

    # Perguntar se quer continuar
    response = input("Deseja continuar com a coleta? (s/N): ").strip().lower()
    if response != 's':
        print("Coleta cancelada pelo usuario.")
        print()
        print("=" * 70)
        print("TESTE PARCIAL CONCLUIDO")
        print("=" * 70)
        return

    # Executar coleta
    results = collector.collect('cagedmov', save=True, verbose=True)

    print()
    print("-" * 70)
    print("6. Resultados da coleta:")
    print("-" * 70)
    for key, df in results.items():
        print(f"   {key}: {len(df):,} registros")
    print()

    # Verificar status apos coleta
    print("-" * 70)
    print("7. Status apos coleta:")
    print("-" * 70)
    status = collector.get_status()
    print(status.to_string())
    print()

    # Ler dados salvos
    print("-" * 70)
    print("8. Leitura dos dados salvos:")
    print("-" * 70)
    df = collector.read('cagedmov')
    print(f"   Registros: {len(df):,}")
    print(f"   Colunas: {len(df.columns)}")
    print(f"   Memoria: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    print()

    print("=" * 70)
    print("TESTE CONCLUIDO!")
    print("=" * 70)


if __name__ == '__main__':
    main()
