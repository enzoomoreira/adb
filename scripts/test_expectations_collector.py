"""
Script de teste para o modulo ExpectationsCollector.
"""

from pathlib import Path
import sys

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from bacen.expectations import (
    ExpectationsCollector,
    EXPECTATIONS_CONFIG,
    list_indicators,
)


def main():
    print("=" * 70)
    print("TESTE DO MODULO EXPECTATIONS COLLECTOR")
    print("=" * 70)
    print()

    # Mostrar indicadores disponiveis
    print("Indicadores disponiveis:")
    for key in list_indicators():
        config = EXPECTATIONS_CONFIG[key]
        print(f"  - {key}: {config['description']}")
    print()

    # Inicializar collector
    data_path = Path(__file__).parent.parent / 'data'
    collector = ExpectationsCollector(data_path)
    print(f"Data path: {data_path}")
    print()

    # Teste 1: Coletar um indicador especifico
    print("-" * 70)
    print("Teste 1: Coletar ipca_anual (limit=50)")
    print("-" * 70)
    df = collector.collect_indicator(
        key='ipca_anual',
        filename='ipca_anual',
        limit=50,
        save=True,
    )
    if not df.empty:
        print(f"Colunas: {list(df.columns)}")
        print(df.head())
    print()

    # Teste 2: Coletar com controle total
    print("-" * 70)
    print("Teste 2: Coletar endpoint selic com controle total (limit=30)")
    print("-" * 70)
    df = collector.collect_endpoint(
        endpoint='selic',
        filename='selic_teste',
        indicator='Selic',
        limit=30,
        save=True,
    )
    if not df.empty:
        print(f"Colunas: {list(df.columns)}")
        print(df.head())
    print()

    # Teste 3: Listar arquivos salvos
    print("-" * 70)
    print("Teste 3: Listar arquivos salvos")
    print("-" * 70)
    files = collector.list_files()
    print(f"Arquivos: {files}")
    print()

    # Teste 4: Status
    print("-" * 70)
    print("Teste 4: Status dos arquivos")
    print("-" * 70)
    status = collector.get_status()
    if not status.empty:
        print(status.to_string())
    print()

    print("=" * 70)
    print("TESTES CONCLUIDOS!")
    print("=" * 70)


if __name__ == '__main__':
    main()
