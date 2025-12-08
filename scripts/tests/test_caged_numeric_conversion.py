"""
Testa conversao robusta de colunas numericas no CAGED.

Problema: alguns meses tem valores como '44' (sem virgula),
outros tem '44,00' (com virgula). O decimal=',' nao resolve
todos os casos.

Solucao: converter colunas numericas com pd.to_numeric apos leitura.
"""

import sys
from pathlib import Path
import tempfile

import pandas as pd
import py7zr
import pyarrow as pa

# Adiciona src ao path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from mte.caged.client import CAGEDClient


# Colunas que podem ter formato inconsistente (com/sem virgula decimal)
NUMERIC_COLUMNS = [
    'horascontratuais',
    'salário',
    'valorsaláriofixo',
]


def convert_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Converte colunas para numerico de forma robusta."""
    for col in columns:
        if col in df.columns:
            # Primeiro substitui virgula por ponto (se houver)
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            # Converte para numerico
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def test_conversion():
    print("=" * 70)
    print("TESTE DE CONVERSAO ROBUSTA")
    print("=" * 70)

    client = CAGEDClient()
    client.connect()

    try:
        # Baixa mes problematico (2023-08)
        print("\nBaixando 2023-08 (mes problematico)...")
        filepath = client._build_filepath("CAGEDMOV", 2023, 8)
        buffer = client.download_to_memory(filepath)

        with tempfile.TemporaryDirectory() as tmpdir:
            with py7zr.SevenZipFile(buffer, mode='r') as archive:
                archive.extractall(path=tmpdir)
            csv_files = list(Path(tmpdir).glob("*.txt")) + list(Path(tmpdir).glob("*.csv"))

            # Leitura COM decimal=',' (comportamento atual)
            df = pd.read_csv(
                csv_files[0],
                encoding='utf-8',
                sep=";",
                decimal=",",
                low_memory=False,
            )

            print(f"\nAntes da conversao:")
            for col in NUMERIC_COLUMNS:
                if col in df.columns:
                    print(f"  {col}: {df[col].dtype} -> {df[col].head(3).tolist()}")

            # Aplica conversao robusta
            df = convert_numeric_columns(df, NUMERIC_COLUMNS)

            print(f"\nDepois da conversao:")
            for col in NUMERIC_COLUMNS:
                if col in df.columns:
                    print(f"  {col}: {df[col].dtype} -> {df[col].head(3).tolist()}")

            # Testa PyArrow
            print("\nTestando conversao para PyArrow...")
            try:
                table = pa.Table.from_pandas(df)
                print("SUCESSO!")
            except Exception as e:
                print(f"ERRO: {e}")
                return False

        # Baixa mes normal (2023-07)
        print("\n" + "-" * 50)
        print("Baixando 2023-07 (mes normal)...")
        filepath = client._build_filepath("CAGEDMOV", 2023, 7)
        buffer = client.download_to_memory(filepath)

        with tempfile.TemporaryDirectory() as tmpdir:
            with py7zr.SevenZipFile(buffer, mode='r') as archive:
                archive.extractall(path=tmpdir)
            csv_files = list(Path(tmpdir).glob("*.txt")) + list(Path(tmpdir).glob("*.csv"))

            df2 = pd.read_csv(
                csv_files[0],
                encoding='utf-8',
                sep=";",
                decimal=",",
                low_memory=False,
            )

            print(f"\nAntes da conversao:")
            for col in NUMERIC_COLUMNS:
                if col in df2.columns:
                    print(f"  {col}: {df2[col].dtype} -> {df2[col].head(3).tolist()}")

            df2 = convert_numeric_columns(df2, NUMERIC_COLUMNS)

            print(f"\nDepois da conversao:")
            for col in NUMERIC_COLUMNS:
                if col in df2.columns:
                    print(f"  {col}: {df2[col].dtype} -> {df2[col].head(3).tolist()}")

        # Testa concatenacao
        print("\n" + "-" * 50)
        print("Testando concatenacao de ambos os meses...")

        combined = pd.concat([df, df2], ignore_index=True)
        print("Tipos apos concatenacao:")
        for col in NUMERIC_COLUMNS:
            if col in combined.columns:
                print(f"  {col}: {combined[col].dtype}")

        print("\nTestando conversao para PyArrow...")
        try:
            table = pa.Table.from_pandas(combined)
            print("SUCESSO!")
            return True
        except Exception as e:
            print(f"ERRO: {e}")
            return False

    finally:
        client.disconnect()


if __name__ == "__main__":
    success = test_conversion()
    print("\n" + "=" * 70)
    if success:
        print("TESTE PASSOU - Conversao robusta funciona!")
    else:
        print("TESTE FALHOU")
    print("=" * 70)
