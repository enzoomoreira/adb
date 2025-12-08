"""
Teste final: simula o fluxo do collector com as correcoes.
"""

import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from mte.caged.client import CAGEDClient


def test_collect_flow():
    """Simula o fluxo de coleta com append."""
    print("=" * 70)
    print("TESTE FINAL: Simulacao do Collector")
    print("=" * 70)

    client = CAGEDClient()
    client.connect()

    try:
        # Baixa 3 meses consecutivos (incluindo os problematicos)
        months = [(2023, 7), (2023, 8), (2023, 9)]
        all_dfs = []

        for year, month in months:
            print(f"\nBaixando {year}-{month:02d}...")
            df = client.get_data("CAGEDMOV", year, month, verbose=False)
            print(f"  Registros: {len(df):,}")
            print(f"  horascontratuais dtype: {df['horascontratuais'].dtype}")
            print(f"  salário dtype: {df['salário'].dtype}")
            all_dfs.append(df)

        # Simula append (concatenacao)
        print("\n" + "-" * 50)
        print("Simulando append (concatenacao de todos os meses)...")

        combined = pd.concat(all_dfs, ignore_index=True)
        print(f"\nTotal de registros: {len(combined):,}")
        print(f"horascontratuais dtype: {combined['horascontratuais'].dtype}")
        print(f"salário dtype: {combined['salário'].dtype}")
        print(f"valorsaláriofixo dtype: {combined['valorsaláriofixo'].dtype}")

        # Testa conversao para PyArrow (o que falha no to_parquet)
        print("\n" + "-" * 50)
        print("Testando conversao para PyArrow...")

        try:
            table = pa.Table.from_pandas(combined)
            print("SUCESSO!")

            # Testa salvar como parquet em memoria
            import io
            buf = io.BytesIO()
            combined.to_parquet(buf, engine='pyarrow', compression='snappy')
            print(f"Parquet size: {len(buf.getvalue()) / 1024 / 1024:.1f} MB")
            return True

        except Exception as e:
            print(f"ERRO: {e}")
            return False

    finally:
        client.disconnect()


if __name__ == "__main__":
    success = test_collect_flow()
    print("\n" + "=" * 70)
    if success:
        print("TESTE PASSOU - Collector deve funcionar corretamente!")
    else:
        print("TESTE FALHOU - Ainda ha problemas")
    print("=" * 70)
