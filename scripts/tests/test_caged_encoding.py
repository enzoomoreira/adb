"""
Testa diferentes encodings para leitura do CAGED.
"""

import sys
from pathlib import Path
import tempfile

import pandas as pd
import py7zr

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from mte.caged.client import CAGEDClient


def test_encoding(encoding: str):
    client = CAGEDClient()
    client.connect()

    try:
        print(f"\n{'='*60}")
        print(f"Testando encoding: {encoding}")
        print("="*60)

        filepath = client._build_filepath("CAGEDMOV", 2023, 8)
        buffer = client.download_to_memory(filepath)

        with tempfile.TemporaryDirectory() as tmpdir:
            with py7zr.SevenZipFile(buffer, mode='r') as archive:
                archive.extractall(path=tmpdir)
            csv_files = list(Path(tmpdir).glob("*.txt")) + list(Path(tmpdir).glob("*.csv"))

            try:
                df = pd.read_csv(
                    csv_files[0],
                    encoding=encoding,
                    sep=";",
                    decimal=",",
                    low_memory=False,
                    nrows=10,
                )

                # Mostra colunas com 'sal'
                print("\nColunas contendo 'sal':")
                for col in df.columns:
                    if 'sal' in col.lower():
                        print(f"  '{col}' - bytes: {col.encode('utf-8')}")

                # Testa se encontra coluna esperada
                if 'salário' in df.columns:
                    print(f"\n'salário' encontrado! Tipo: {df['salário'].dtype}")
                else:
                    print(f"\n'salário' NAO encontrado")

                return True

            except Exception as e:
                print(f"Erro: {e}")
                return False

    finally:
        client.disconnect()


if __name__ == "__main__":
    for enc in ['latin-1', 'utf-8', 'cp1252', 'iso-8859-1']:
        test_encoding(enc)
