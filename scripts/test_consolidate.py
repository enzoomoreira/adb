"""
Script para testar a consolidacao com cdi_anualizado.

Uso: uv run scripts/test_consolidate.py
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
from bacen.sgs import SGSCollector


def main():
    print("=" * 70)
    print("TESTE DE CONSOLIDACAO COM CDI ANUALIZADO")
    print("=" * 70)

    data_path = Path(__file__).parent.parent / "data"
    collector = SGSCollector(data_path)

    # Consolidar apenas dados diarios
    print("\nConsolidando sgs/daily...")
    results = collector.consolidate(subdirs='sgs/daily', save=True, verbose=True)

    df = results.get('sgs/daily')
    if df is None or df.empty:
        print("Erro: DataFrame vazio!")
        return

    print("\n" + "=" * 70)
    print("RESULTADO")
    print("=" * 70)

    print(f"\nColunas: {df.columns.tolist()}")
    print(f"\nUltimos 10 registros (cdi, cdi_anualizado, selic):")

    cols = ['cdi', 'cdi_anualizado', 'selic']
    available_cols = [c for c in cols if c in df.columns]
    print(df[available_cols].tail(10).to_string())

    # Verificar diferenca
    if 'cdi_anualizado' in df.columns and 'selic' in df.columns:
        recent = df.tail(30).dropna(subset=['cdi_anualizado', 'selic'])
        diff = recent['cdi_anualizado'] - recent['selic']
        print(f"\nDiferenca cdi_anualizado - selic (ultimos 30 dias):")
        print(f"  Media: {diff.mean():.4f} p.p.")

    # Verificar arquivo salvo
    parquet_path = data_path / "processed" / "sgs_daily_consolidated.parquet"
    if parquet_path.exists():
        saved_df = pd.read_parquet(parquet_path)
        print(f"\nArquivo salvo: {parquet_path}")
        print(f"Colunas no arquivo: {saved_df.columns.tolist()}")
        assert 'cdi_anualizado' in saved_df.columns, "cdi_anualizado nao esta no arquivo!"
        print("\nSUCESSO: cdi_anualizado presente no arquivo consolidado!")


if __name__ == "__main__":
    main()
