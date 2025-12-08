"""
Script para coleta de dados CAGED.

Executa coleta incremental:
- Primeira execucao: baixa historico completo (2020+)
- Execucoes seguintes: apenas meses novos

Uso: uv run scripts/collect_caged.py [indicador]

Exemplos:
  uv run scripts/collect_caged.py           # Coleta todos (cagedmov, cagedfor, cagedexc)
  uv run scripts/collect_caged.py cagedmov  # Apenas movimentacoes
"""

from pathlib import Path
import sys
import argparse

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mte.caged import CAGEDCollector, list_indicators, get_available_periods


def main():
    parser = argparse.ArgumentParser(description='Coleta dados CAGED')
    parser.add_argument(
        'indicator',
        nargs='?',
        default='all',
        help='Indicador a coletar (cagedmov, cagedfor, cagedexc, all)'
    )
    args = parser.parse_args()

    print("=" * 70)
    print("COLETA DE DADOS CAGED")
    print("Ministerio do Trabalho e Emprego")
    print("=" * 70)
    print()

    # Info
    periods = get_available_periods()
    print(f"Periodos disponiveis: {len(periods)} meses")
    print(f"De: {periods[0][0]}-{periods[0][1]:02d}")
    print(f"Ate: {periods[-1][0]}-{periods[-1][1]:02d}")
    print()

    print(f"Indicadores disponiveis: {list_indicators()}")
    print(f"Indicador selecionado: {args.indicator}")
    print()

    # Inicializar collector
    data_path = Path(__file__).parent.parent / 'data'
    collector = CAGEDCollector(data_path)

    # Status antes
    print("-" * 70)
    print("STATUS ANTES DA COLETA:")
    print("-" * 70)
    status = collector.get_status()
    if status.empty:
        print("Nenhum arquivo salvo")
    else:
        print(status.to_string())
    print()

    # Executar coleta
    print("-" * 70)
    print("INICIANDO COLETA:")
    print("-" * 70)
    print()

    results = collector.collect(args.indicator, save=True, verbose=True)

    # Status depois
    print()
    print("-" * 70)
    print("STATUS APOS COLETA:")
    print("-" * 70)
    status = collector.get_status()
    print(status.to_string())

    # Resumo
    print()
    print("-" * 70)
    print("RESUMO:")
    print("-" * 70)
    for key, count in results.items():
        print(f"  {key}: {count:,} novos registros")

    print()
    print("=" * 70)
    print("COLETA CONCLUIDA!")
    print("=" * 70)


if __name__ == '__main__':
    main()
