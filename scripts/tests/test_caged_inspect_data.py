"""
Inspeciona os arquivos parquet do CAGED salvos.
"""

from pathlib import Path
import pandas as pd

data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "mte" / "caged"

print("=" * 80)
print("INSPECAO DOS ARQUIVOS CAGED")
print("=" * 80)

for name in ['cagedmov', 'cagedfor', 'cagedexc']:
    filepath = data_path / f"{name}.parquet"

    print(f"\n{'='*80}")
    print(f"ARQUIVO: {name}.parquet")
    print("="*80)

    if not filepath.exists():
        print("  ARQUIVO NAO EXISTE")
        continue

    df = pd.read_parquet(filepath)

    print(f"\nShape: {df.shape}")
    print(f"Memoria: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")

    print(f"\nIndice:")
    print(f"  Tipo: {type(df.index).__name__}")
    print(f"  dtype: {df.index.dtype}")
    print(f"  Min: {df.index.min()}, Max: {df.index.max()}")
    print(f"  Valores unicos: {df.index.nunique()}")
    print(f"  Duplicados: {df.index.duplicated().sum()}")

    print(f"\nColunas ({len(df.columns)}):")
    for col in df.columns:
        print(f"  {col}: {df[col].dtype}")

    print(f"\nPeriodos (ano_ref, mes_ref):")
    if 'ano_ref' in df.columns and 'mes_ref' in df.columns:
        periodos = df.groupby(['ano_ref', 'mes_ref']).size()
        print(f"  Total de periodos: {len(periodos)}")
        print(f"  Primeiro: {periodos.index[0]}")
        print(f"  Ultimo: {periodos.index[-1]}")
        print(f"\n  Registros por periodo (primeiros 5):")
        for (ano, mes), count in periodos.head().items():
            print(f"    {ano}-{mes:02d}: {count:,}")
        print(f"  ...")
        print(f"  Registros por periodo (ultimos 5):")
        for (ano, mes), count in periodos.tail().items():
            print(f"    {ano}-{mes:02d}: {count:,}")

    print(f"\nPrimeiras 3 linhas:")
    print(df.head(3).to_string())

    print(f"\nUltimas 3 linhas:")
    print(df.tail(3).to_string())
