"""
Verifica os nomes exatos das colunas do CAGED.
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
        print("Baixando 2023-08...")
        filepath = client._build_filepath("CAGEDMOV", 2023, 8)
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
                nrows=10,
            )

            print("\nColunas do DataFrame:")
            for i, col in enumerate(df.columns):
                print(f"  {i}: '{col}' (bytes: {col.encode('utf-8')})")

            # Testa busca por substring
            print("\nColunas contendo 'sal':")
            for col in df.columns:
                if 'sal' in col.lower():
                    print(f"  '{col}'")

            print("\nColunas contendo 'hora':")
            for col in df.columns:
                if 'hora' in col.lower():
                    print(f"  '{col}'")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
