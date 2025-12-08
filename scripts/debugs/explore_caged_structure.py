"""
Script para explorar a estrutura dos dados CAGED.

Baixa um mes de cada tipo (MOV, FOR, EXC) e analisa:
- Colunas e tipos
- Valores unicos de colunas categoricas
- Estatisticas basicas
- Diferenca entre os tipos de arquivo

Uso: uv run scripts/explore_caged_structure.py
"""

from pathlib import Path
import sys

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mte.caged import CAGEDClient, CAGED_CONFIG
import pandas as pd


def analyze_dataframe(df: pd.DataFrame, name: str):
    """Analisa estrutura de um DataFrame."""
    print(f"\n{'=' * 70}")
    print(f"ANALISE: {name}")
    print(f"{'=' * 70}")

    print(f"\nShape: {df.shape[0]:,} linhas x {df.shape[1]} colunas")

    # Memoria
    mem_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
    print(f"Memoria: {mem_mb:.2f} MB")

    # Colunas e tipos
    print(f"\n{'Coluna':<30} {'Tipo':<15} {'Nulls':<10} {'Unicos':<10}")
    print("-" * 70)
    for col in df.columns:
        dtype = str(df[col].dtype)
        nulls = df[col].isna().sum()
        unicos = df[col].nunique()
        print(f"{col:<30} {dtype:<15} {nulls:<10} {unicos:<10}")

    # Colunas categoricas (poucos valores unicos)
    print("\n" + "-" * 70)
    print("VALORES DE COLUNAS CATEGORICAS:")
    print("-" * 70)

    categorical_cols = [
        'região', 'uf', 'seção', 'categoria', 'graudeinstrução',
        'raçacor', 'sexo', 'tipoempregador', 'tipoestabelecimento',
        'tipomovimentação', 'tipodedeficiência', 'indtrabintermitente',
        'indtrabparcial', 'indicadoraprendiz', 'indicadordeforadoprazo',
        'saldomovimentação'
    ]

    for col in categorical_cols:
        if col in df.columns:
            valores = df[col].value_counts().head(10)
            print(f"\n{col}:")
            for val, count in valores.items():
                pct = count / len(df) * 100
                print(f"  {val}: {count:,} ({pct:.1f}%)")


def compare_file_types(dfs: dict):
    """Compara estrutura entre tipos de arquivo."""
    print(f"\n{'=' * 70}")
    print("COMPARACAO ENTRE TIPOS DE ARQUIVO")
    print(f"{'=' * 70}")

    # Colunas em comum e exclusivas
    all_cols = set()
    cols_by_type = {}

    for name, df in dfs.items():
        cols = set(df.columns)
        cols_by_type[name] = cols
        all_cols.update(cols)

    common_cols = cols_by_type['CAGEDMOV'] & cols_by_type['CAGEDFOR'] & cols_by_type['CAGEDEXC']
    print(f"\nColunas em comum: {len(common_cols)}")

    for name, cols in cols_by_type.items():
        exclusive = cols - common_cols
        if exclusive:
            print(f"\nColunas exclusivas de {name}: {exclusive}")

    # Quantidade de registros
    print("\n" + "-" * 70)
    print("QUANTIDADE DE REGISTROS:")
    print("-" * 70)
    for name, df in dfs.items():
        print(f"  {name}: {len(df):,}")


def main():
    print("=" * 70)
    print("EXPLORACAO DA ESTRUTURA DOS DADOS CAGED")
    print("=" * 70)

    client = CAGEDClient(timeout=300)
    client.connect()

    # Baixar um mes de cada tipo
    year, month = 2024, 1
    dfs = {}

    try:
        for key, config in CAGED_CONFIG.items():
            prefix = config['prefix']
            print(f"\nBaixando {prefix} {year}-{month:02d}...")
            df = client.get_data(prefix, year, month, verbose=True)
            if not df.empty:
                dfs[prefix] = df

    finally:
        client.disconnect()

    # Analisar cada tipo
    for name, df in dfs.items():
        analyze_dataframe(df, name)

    # Comparar tipos
    if len(dfs) == 3:
        compare_file_types(dfs)

    # Salvar sample para inspecao manual
    print("\n" + "=" * 70)
    print("SALVANDO SAMPLES")
    print("=" * 70)

    temp_path = Path(__file__).parent.parent / 'temp'
    temp_path.mkdir(exist_ok=True)

    for name, df in dfs.items():
        sample_path = temp_path / f"sample_{name.lower()}.csv"
        df.head(100).to_csv(sample_path, index=False)
        print(f"Salvo: {sample_path}")

    print("\n" + "=" * 70)
    print("EXPLORACAO CONCLUIDA!")
    print("=" * 70)


if __name__ == '__main__':
    main()
