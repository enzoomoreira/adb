"""
Script para testar download de um mes de dados CAGED.

Baixa um unico mes para verificar:
- Download em memoria funciona
- Extracao do 7z funciona
- Leitura do CSV funciona
- Estrutura dos dados

Uso: uv run scripts/test_caged_download.py
"""

from pathlib import Path
import sys

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mte.caged import CAGEDClient


def main():
    print("=" * 70)
    print("TESTE DE DOWNLOAD - MTE/CAGED")
    print("=" * 70)
    print()

    client = CAGEDClient(timeout=120)

    # Conectar
    print("1. Conectando ao FTP...")
    client.connect()
    print("   OK")
    print()

    # Baixar um mes de teste (janeiro 2024 - mais recente e menor)
    year, month = 2024, 1
    prefix = "CAGEDMOV"

    print(f"2. Baixando {prefix} {year}-{month:02d}...")
    print(f"   Caminho: {client._build_filepath(prefix, year, month)}")
    print()

    try:
        df = client.get_data(prefix, year, month, verbose=True)

        if df.empty:
            print("   ERRO: DataFrame vazio")
            return

        print()
        print("3. Estrutura dos dados:")
        print(f"   Shape: {df.shape}")
        print(f"   Colunas ({len(df.columns)}):")
        for col in df.columns:
            dtype = df[col].dtype
            nulls = df[col].isna().sum()
            print(f"     - {col}: {dtype} ({nulls} nulls)")

        print()
        print("4. Primeiras linhas:")
        print(df.head(3).to_string())

        print()
        print("5. Ultimas linhas:")
        print(df.tail(3).to_string())

        print()
        print("6. Memoria utilizada:")
        mem_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        print(f"   {mem_mb:.2f} MB")

    except Exception as e:
        print(f"   ERRO: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print()
        print("7. Desconectando...")
        client.disconnect()
        print("   OK")

    print()
    print("=" * 70)
    print("DOWNLOAD TESTADO!")
    print("=" * 70)


if __name__ == '__main__':
    main()
