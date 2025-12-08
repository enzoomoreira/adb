"""
Debug script para investigar problemas com series PTAX.

Problemas identificados:
- Dolar PTAX (10813): Dados pararam em 2019-12-31
- Euro PTAX (21619): Apenas dados de 1998-1999

Hipoteses:
1. Erro no chunking (loop nao continua apos 2019)
2. API bloqueando requests
3. Codigo SGS errado
4. Dados realmente nao existem
"""

from bcb import sgs
import pandas as pd
from datetime import datetime

print("=" * 70)
print("DEBUG: SERIES PTAX")
print("=" * 70)

# Codigos a testar
CODIGOS = {
    'dolar_ptax': 10813,
    'euro_ptax': 21619,
    'selic': 432,  # Para comparacao (funcionou parcialmente)
    'cdi': 12,     # Para comparacao (funcionou bem)
}

def test_serie_direta(nome, codigo, start, end):
    """Testa download direto de uma serie."""
    print(f"\n[{nome}] Codigo {codigo}: {start} a {end}")
    try:
        df = sgs.get({nome: codigo}, start=start, end=end)
        if df.empty:
            print(f"  -> VAZIO (nenhum dado retornado)")
        else:
            print(f"  -> OK: {len(df)} registros")
            print(f"     Periodo: {df.index.min()} a {df.index.max()}")
        return df
    except Exception as e:
        print(f"  -> ERRO: {e}")
        return pd.DataFrame()


print("\n" + "=" * 70)
print("TESTE 1: Download direto por decada")
print("=" * 70)

for nome, codigo in CODIGOS.items():
    print(f"\n{'='*50}")
    print(f"Serie: {nome} (codigo {codigo})")
    print('='*50)

    # Testar cada decada
    for start_year in range(1980, 2030, 10):
        end_year = min(start_year + 9, 2025)
        test_serie_direta(nome, codigo, f'{start_year}-01-01', f'{end_year}-12-31')


print("\n" + "=" * 70)
print("TESTE 2: Anos recentes (2020-2025) - FOCO NO PROBLEMA")
print("=" * 70)

for nome, codigo in [('dolar_ptax', 10813), ('euro_ptax', 21619)]:
    print(f"\n{'='*50}")
    print(f"Serie: {nome}")
    print('='*50)

    # Testar ano a ano
    for year in range(2018, 2026):
        test_serie_direta(nome, codigo, f'{year}-01-01', f'{year}-12-31')


print("\n" + "=" * 70)
print("TESTE 3: Ultimos 30 dias (dados recentissimos)")
print("=" * 70)

for nome, codigo in CODIGOS.items():
    test_serie_direta(nome, codigo, '2025-11-01', '2025-12-31')


print("\n" + "=" * 70)
print("TESTE 4: Parametro 'last' (ultimos N registros)")
print("=" * 70)

for nome, codigo in CODIGOS.items():
    print(f"\n[{nome}] Ultimos 10 registros:")
    try:
        df = sgs.get({nome: codigo}, last=10)
        if df.empty:
            print("  -> VAZIO")
        else:
            print(f"  -> {len(df)} registros")
            print(df.tail())
    except Exception as e:
        print(f"  -> ERRO: {e}")


print("\n" + "=" * 70)
print("TESTE 5: Sem parametros (deixar API decidir)")
print("=" * 70)

for nome, codigo in [('dolar_ptax', 10813), ('euro_ptax', 21619)]:
    print(f"\n[{nome}] Download sem restricao de data:")
    try:
        df = sgs.get({nome: codigo})
        if df.empty:
            print("  -> VAZIO")
        else:
            print(f"  -> {len(df)} registros")
            print(f"     Periodo: {df.index.min()} a {df.index.max()}")
    except Exception as e:
        print(f"  -> ERRO: {e}")


print("\n" + "=" * 70)
print("CONCLUSAO")
print("=" * 70)
print("""
Analise os resultados acima para identificar:
1. Se os dados existem na API para periodos recentes
2. Se ha erro especifico em algum periodo
3. Se o codigo SGS esta correto
4. Se ha limite de requests sendo atingido
""")
