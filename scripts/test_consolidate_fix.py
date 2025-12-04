"""
Script para testar a correcao do DatetimeIndex na consolidacao de expectations.
Reconsolida os dados e verifica se o indice agora e datetime.
"""

from pathlib import Path
import pandas as pd
import sys

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from bacen import ExpectationsCollector

data_path = Path(__file__).parent.parent / 'data'

print("=" * 70)
print("TESTANDO CORRECAO DA CONSOLIDACAO")
print("=" * 70)

# Reconsolidar dados
collector = ExpectationsCollector(data_path)
results = collector.consolidate(verbose=True)

# Verificar resultado
print("\n" + "=" * 70)
print("VERIFICANDO RESULTADO")
print("=" * 70)

df = results.get('expectations', pd.DataFrame())

if not df.empty:
    print(f"\nShape: {df.shape}")
    print(f"Index type: {type(df.index).__name__}")
    print(f"Index dtype: {df.index.dtype}")
    print(f"Index name: {df.index.name}")
    print(f"Index range: {df.index.min()} a {df.index.max()}")

    print(f"\nColunas: {list(df.columns)}")

    print(f"\nPrimeiras linhas:")
    print(df.head(3).to_string())

    # Testar fatiamento temporal
    print("\n" + "-" * 70)
    print("TESTE DE FATIAMENTO TEMPORAL")
    print("-" * 70)

    try:
        nov_2025 = df.loc['2025-11']
        print(f"df.loc['2025-11']: {len(nov_2025):,} registros")

        # Filtrar por fonte
        ipca = nov_2025[nov_2025['_source'] == 'ipca_anual']
        print(f"  - ipca_anual em nov/2025: {len(ipca):,} registros")

        print("\nSUCESSO! Fatiamento temporal funcionando.")
    except Exception as e:
        print(f"ERRO no fatiamento: {e}")
else:
    print("DataFrame vazio!")

print("\n" + "=" * 70)
