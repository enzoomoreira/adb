"""
Script para testar a correcao do DatetimeIndex nos dados de expectations.
Testa duas abordagens:
  A) Corrigir na consolidacao (pos-processamento)
  B) Corrigir antes de salvar (nos dados raw)
"""

from pathlib import Path
import pandas as pd

data_path = Path(__file__).parent.parent / 'data'
raw_path = data_path / 'raw' / 'expectations'

print("=" * 70)
print("TESTANDO CORRECAO DO DATETIMEINDEX")
print("=" * 70)

# Carregar um arquivo raw para teste
df = pd.read_parquet(raw_path / 'ipca_anual.parquet')
print(f"\nDados originais:")
print(f"  Shape: {df.shape}")
print(f"  Index: {df.index.dtype}")
print(f"  Coluna Data: {df['Data'].dtype}")

# =========================================================================
# OPCAO A: Corrigir na consolidacao
# =========================================================================
print("\n" + "-" * 70)
print("OPCAO A: Corrigir na consolidacao (set_index)")
print("-" * 70)

df_a = df.copy()
df_a = df_a.set_index('Data').sort_index()

print(f"  Index type: {type(df_a.index).__name__}")
print(f"  Index dtype: {df_a.index.dtype}")
print(f"  Index range: {df_a.index.min()} a {df_a.index.max()}")
print(f"  Colunas: {list(df_a.columns)}")
print(f"\nPrimeiras linhas:")
print(df_a.head(3).to_string())

# Problema: indices duplicados?
print(f"\n  Indices duplicados: {df_a.index.duplicated().sum():,}")

# =========================================================================
# OPCAO B: Manter Data como coluna, usar indice numerico
# =========================================================================
print("\n" + "-" * 70)
print("OPCAO B: Manter Data como coluna (atual)")
print("-" * 70)
print("Pros: Nao perde informacao, permite multiplos registros por data")
print("Cons: Nao segue padrao do projeto (DatetimeIndex)")

# =========================================================================
# OPCAO C: Criar indice datetime mas manter Data como coluna
# =========================================================================
print("\n" + "-" * 70)
print("OPCAO C: Indice datetime + manter coluna Data")
print("-" * 70)

df_c = df.copy()
df_c.index = pd.DatetimeIndex(df_c['Data'])
df_c.index.name = 'Date'
df_c = df_c.sort_index()

print(f"  Index type: {type(df_c.index).__name__}")
print(f"  Index dtype: {df_c.index.dtype}")
print(f"  Coluna 'Data' preservada: {'Data' in df_c.columns}")
print(f"\nPrimeiras linhas:")
print(df_c.head(3).to_string())

# =========================================================================
# ANALISE: Por que existem multiplos registros por data?
# =========================================================================
print("\n" + "-" * 70)
print("ANALISE: Registros por data")
print("-" * 70)

registros_por_data = df.groupby('Data').size()
print(f"  Datas unicas: {len(registros_por_data):,}")
print(f"  Total registros: {len(df):,}")
print(f"  Media de registros por data: {registros_por_data.mean():.1f}")
print(f"  Max registros em uma data: {registros_por_data.max()}")

# Exemplo de uma data com multiplos registros
data_exemplo = df['Data'].iloc[0]
registros_data = df[df['Data'] == data_exemplo]
print(f"\nExemplo - Registros em {data_exemplo.strftime('%Y-%m-%d')}:")
print(registros_data[['Indicador', 'DataReferencia', 'tipoCalculo', 'Mediana']].to_string())

print("\n" + "=" * 70)
print("CONCLUSAO")
print("=" * 70)
print("""
Os dados de Expectations tem MULTIPLOS registros por data porque:
- Cada data tem projecoes para diferentes anos de referencia (2025, 2026, 2027...)
- Cada data tem diferentes tipos de calculo (C, M, etc)

RECOMENDACAO:
- Para arquivos RAW: manter estrutura atual (indice numerico, coluna Data)
- Para CONSOLIDADO: converter Data para indice apos concatenacao
  Isso permite filtrar facilmente por periodo de coleta.

Codigo sugerido para consolidate():
    if 'Data' in df.columns and not df.empty:
        df = df.set_index('Data').sort_index()
""")
