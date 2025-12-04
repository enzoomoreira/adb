"""
Script para explorar a estrutura dos dados de expectations.
Objetivo: Entender onde a coluna 'Data' perde o formato datetime.
"""

from pathlib import Path
import pandas as pd

# Paths
data_path = Path(__file__).parent.parent / 'data'
raw_path = data_path / 'raw' / 'expectations'
processed_path = data_path / 'processed'

print("=" * 70)
print("EXPLORANDO ESTRUTURA DOS DADOS DE EXPECTATIONS")
print("=" * 70)

# 1. Verificar arquivos raw disponiveis
print("\n1. ARQUIVOS RAW DISPONIVEIS")
print("-" * 70)
raw_files = list(raw_path.glob('*.parquet'))
for f in raw_files:
    print(f"  - {f.name}")

# 2. Analisar estrutura de um arquivo raw
print("\n2. ESTRUTURA DE UM ARQUIVO RAW (ipca_anual)")
print("-" * 70)
if (raw_path / 'ipca_anual.parquet').exists():
    df_raw = pd.read_parquet(raw_path / 'ipca_anual.parquet')
    print(f"Shape: {df_raw.shape}")
    print(f"Index type: {type(df_raw.index).__name__}")
    print(f"Index dtype: {df_raw.index.dtype}")
    print(f"Index range: {df_raw.index.min()} a {df_raw.index.max()}")
    print(f"\nColunas e tipos:")
    for col in df_raw.columns:
        print(f"  {col:25} -> {df_raw[col].dtype}")
    print(f"\nPrimeiras linhas:")
    print(df_raw.head(3).to_string())
else:
    print("Arquivo nao encontrado")

# 3. Analisar arquivo consolidado
print("\n\n3. ESTRUTURA DO ARQUIVO CONSOLIDADO")
print("-" * 70)
consolidated_file = processed_path / 'expectations_consolidated.parquet'
if consolidated_file.exists():
    df_consolidated = pd.read_parquet(consolidated_file)
    print(f"Shape: {df_consolidated.shape}")
    print(f"Index type: {type(df_consolidated.index).__name__}")
    print(f"Index dtype: {df_consolidated.index.dtype}")
    print(f"Index range: {df_consolidated.index.min()} a {df_consolidated.index.max()}")
    print(f"\nColunas e tipos:")
    for col in df_consolidated.columns:
        print(f"  {col:25} -> {df_consolidated[col].dtype}")
    print(f"\nPrimeiras linhas:")
    print(df_consolidated.head(3).to_string())
else:
    print("Arquivo nao encontrado")

# 4. Comparacao
print("\n\n4. DIAGNOSTICO")
print("-" * 70)
if (raw_path / 'ipca_anual.parquet').exists() and consolidated_file.exists():
    print("Arquivo RAW:")
    print(f"  - Indice e datetime? {pd.api.types.is_datetime64_any_dtype(df_raw.index)}")
    print(f"  - Coluna 'Data' existe? {'Data' in df_raw.columns}")
    if 'Data' in df_raw.columns:
        print(f"  - Tipo da coluna 'Data': {df_raw['Data'].dtype}")

    print("\nArquivo CONSOLIDADO:")
    print(f"  - Indice e datetime? {pd.api.types.is_datetime64_any_dtype(df_consolidated.index)}")
    print(f"  - Coluna 'Data' existe? {'Data' in df_consolidated.columns}")
    if 'Data' in df_consolidated.columns:
        print(f"  - Tipo da coluna 'Data': {df_consolidated['Data'].dtype}")

print("\n" + "=" * 70)
