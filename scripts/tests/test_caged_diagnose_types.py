"""
Diagnostica inconsistencias de tipos nos dados do CAGED.

Baixa varios meses e verifica se os tipos sao consistentes.
"""

import sys
from pathlib import Path
import tempfile

import pandas as pd
import py7zr

# Adiciona src ao path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from mte.caged.client import CAGEDClient


def analyze_month(client: CAGEDClient, year: int, month: int) -> dict:
    """Analisa tipos de um mes especifico."""
    filepath = client._build_filepath("CAGEDMOV", year, month)

    try:
        buffer = client.download_to_memory(filepath)

        with tempfile.TemporaryDirectory() as tmpdir:
            with py7zr.SevenZipFile(buffer, mode='r') as archive:
                archive.extractall(path=tmpdir)

            csv_files = list(Path(tmpdir).glob("*.txt")) + list(Path(tmpdir).glob("*.csv"))
            csv_path = csv_files[0]

            # Le com decimal=','
            df = pd.read_csv(
                csv_path,
                encoding='latin-1',
                sep=";",
                decimal=",",
                low_memory=False,
                nrows=1000,  # Amostra para ser rapido
            )

            # Analisa coluna horascontratuais
            col = df['horascontratuais']
            sample_values = col.dropna().head(5).tolist()

            # Verifica valores unicos problematicos
            if col.dtype == 'object':
                unique_types = set(type(v).__name__ for v in col.dropna().head(100))
            else:
                unique_types = {col.dtype.name}

            return {
                'year': year,
                'month': month,
                'dtype': str(col.dtype),
                'sample': sample_values,
                'unique_types': unique_types,
                'nulls': col.isna().sum(),
                'status': 'OK' if col.dtype == 'float64' else 'PROBLEMA',
            }

    except Exception as e:
        return {
            'year': year,
            'month': month,
            'error': str(e),
            'status': 'ERRO',
        }


def main():
    print("=" * 70)
    print("DIAGNOSTICO DE TIPOS - CAGED horascontratuais")
    print("=" * 70)

    client = CAGEDClient()
    client.connect()

    # Meses para testar (foco em 2023, onde o erro ocorre)
    months_to_check = [
        (2023, 7),
        (2023, 8),
        (2023, 9),
        (2023, 10),
        (2023, 11),
        (2023, 12),
        (2024, 1),
        (2024, 6),
    ]

    results = []

    try:
        for year, month in months_to_check:
            print(f"\nAnalisando {year}-{month:02d}...", end=" ", flush=True)
            result = analyze_month(client, year, month)
            results.append(result)

            if 'error' in result:
                print(f"ERRO: {result['error']}")
            else:
                print(f"{result['dtype']} - {result['status']}")
                if result['status'] == 'PROBLEMA':
                    print(f"  Tipos encontrados: {result['unique_types']}")
                    print(f"  Amostra: {result['sample']}")

    finally:
        client.disconnect()

    # Resumo
    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)

    problemas = [r for r in results if r.get('status') == 'PROBLEMA']
    if problemas:
        print(f"\nMeses com problema ({len(problemas)}):")
        for p in problemas:
            print(f"  {p['year']}-{p['month']:02d}: {p['dtype']}")
    else:
        print("\nTodos os meses testados tem tipo float64")

    # Teste de concatenacao
    print("\n" + "-" * 70)
    print("TESTE DE CONCATENACAO")
    print("-" * 70)

    client.connect()
    try:
        dfs = []
        for year, month in [(2023, 8), (2023, 9)]:
            print(f"Baixando {year}-{month:02d} completo...")
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
                )
                print(f"  horascontratuais dtype: {df['horascontratuais'].dtype}")
                print(f"  Registros: {len(df):,}")
                dfs.append(df)

        print("\nConcatenando...")
        combined = pd.concat(dfs, ignore_index=True)
        print(f"Combined horascontratuais dtype: {combined['horascontratuais'].dtype}")

        print("\nTestando conversao para PyArrow...")
        import pyarrow as pa
        try:
            table = pa.Table.from_pandas(combined)
            print("SUCESSO!")
        except Exception as e:
            print(f"ERRO: {e}")

            # Investigar valores problematicos
            print("\nInvestigando valores problematicos...")
            col = combined['horascontratuais']
            if col.dtype == 'object':
                types_found = {}
                for i, v in enumerate(col):
                    t = type(v).__name__
                    if t not in types_found:
                        types_found[t] = {'count': 0, 'examples': [], 'indices': []}
                    types_found[t]['count'] += 1
                    if len(types_found[t]['examples']) < 3:
                        types_found[t]['examples'].append(v)
                        types_found[t]['indices'].append(i)

                print("Tipos encontrados na coluna:")
                for t, info in types_found.items():
                    print(f"  {t}: {info['count']:,} ocorrencias")
                    print(f"    Exemplos: {info['examples']}")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
