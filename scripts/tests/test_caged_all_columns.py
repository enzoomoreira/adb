"""
Lista todas as colunas do CAGED e seus tipos para identificar problemas.
"""

import sys
from pathlib import Path
import tempfile

import pandas as pd
import py7zr

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from mte.caged.client import CAGEDClient


def main():
    client = CAGEDClient()
    client.connect()

    try:
        # Compara dois meses
        months = [(2023, 7), (2023, 8)]
        dfs = {}

        for year, month in months:
            print(f"Baixando {year}-{month:02d}...")
            filepath = client._build_filepath("CAGEDMOV", year, month)
            buffer = client.download_to_memory(filepath)

            with tempfile.TemporaryDirectory() as tmpdir:
                with py7zr.SevenZipFile(buffer, mode='r') as archive:
                    archive.extractall(path=tmpdir)
                csv_files = list(Path(tmpdir).glob("*.txt")) + list(Path(tmpdir).glob("*.csv"))

                df = pd.read_csv(
                    csv_files[0],
                    encoding='latin-1',
                    sep=";",
                    decimal=",",
                    low_memory=False,
                    nrows=1000,
                )
                dfs[f"{year}-{month:02d}"] = df

        print("\n" + "=" * 80)
        print("COMPARACAO DE TIPOS POR COLUNA")
        print("=" * 80)

        # Compara tipos
        df1 = dfs["2023-07"]
        df2 = dfs["2023-08"]

        print(f"\n{'Coluna':<30} {'2023-07':<15} {'2023-08':<15} {'Problema'}")
        print("-" * 80)

        different_cols = []
        for col in df1.columns:
            if col in df2.columns:
                t1 = str(df1[col].dtype)
                t2 = str(df2[col].dtype)
                problema = "SIM" if t1 != t2 else ""
                if problema:
                    different_cols.append(col)
                print(f"{col:<30} {t1:<15} {t2:<15} {problema}")

        print("\n" + "=" * 80)
        print(f"COLUNAS COM TIPOS DIFERENTES: {len(different_cols)}")
        print("=" * 80)

        for col in different_cols:
            print(f"\n{col}:")
            print(f"  2023-07: {df1[col].dtype} -> {df1[col].head(3).tolist()}")
            print(f"  2023-08: {df2[col].dtype} -> {df2[col].head(3).tolist()}")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
