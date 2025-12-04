"""
Script de teste para o modulo SGSCollector.
"""

from pathlib import Path
import sys

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from bacen.sgs import (
    SGSCollector,
    INDICATORS,
    list_indicators,
    get_indicator_config,
)


def main():
    print("=" * 70)
    print("TESTE DO MODULO SGS COLLECTOR")
    print("=" * 70)
    print()

    # Mostrar indicadores disponiveis
    print("Indicadores disponiveis:")
    for key in list_indicators():
        config = get_indicator_config(key)
        print(f"  - {key}: {config['name']} ({config['frequency']})")
    print()

    # Inicializar collector
    data_path = Path(__file__).parent.parent / 'data'
    collector = SGSCollector(data_path)
    print(f"Data path: {data_path}")
    print()

    # Teste 1: Coletar um indicador especifico (apenas verificar que funciona)
    print("-" * 70)
    print("Teste 1: Coletar selic (verificacao)")
    print("-" * 70)
    df = collector.collect_indicator(
        key='selic',
        filename='selic_teste',
        save=True,
        verbose=True,
    )
    if not df.empty:
        print(f"Registros: {len(df)}")
        print(f"Colunas: {list(df.columns)}")
        print(df.tail())
    print()

    # Teste 2: Listar arquivos salvos
    print("-" * 70)
    print("Teste 2: Listar arquivos salvos (daily)")
    print("-" * 70)
    files = collector.list_files(subdir='daily')
    print(f"Arquivos daily: {files}")
    print()

    # Teste 3: Ler arquivo
    print("-" * 70)
    print("Teste 3: Ler arquivo selic_teste")
    print("-" * 70)
    df = collector.read('selic_teste', subdir='daily')
    if not df.empty:
        print(f"Registros: {len(df)}")
        print(f"Periodo: {df.index.min().date()} a {df.index.max().date()}")
    print()

    # Teste 4: Status
    print("-" * 70)
    print("Teste 4: Status dos indicadores")
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
