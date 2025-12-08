"""
Testa a correcao do problema de conversao decimal no CAGED.

O erro original:
ArrowInvalid: ("Could not convert '44,00' with type str: tried to convert to double",
'Conversion failed for column horascontratuais with type object')

O problema: CAGED usa virgula como separador decimal (padrao BR),
mas pd.read_csv nao esta configurado para isso.

Solucao: adicionar decimal=',' no read_csv
"""

import sys
from pathlib import Path
from io import StringIO

import pandas as pd
import pyarrow as pa

# Simula dados do CAGED com virgula decimal
SAMPLE_CSV = """competencia;regiao;uf;horascontratuais;salario
202301;1;35;44,00;1500,50
202301;1;35;40,00;2000,00
202301;2;33;44,00;1320,00
"""

def test_sem_decimal_param():
    """Teste SEM decimal=',' - deve falhar ao salvar parquet."""
    print("=" * 60)
    print("TESTE 1: Leitura SEM decimal=',' (comportamento atual)")
    print("=" * 60)

    df = pd.read_csv(StringIO(SAMPLE_CSV), sep=";")

    print(f"\nTipos das colunas:")
    print(df.dtypes)

    print(f"\nValores de horascontratuais:")
    print(df['horascontratuais'].tolist())

    print(f"\nTentando converter para PyArrow...")
    try:
        table = pa.Table.from_pandas(df)
        print("SUCESSO - Converteu para PyArrow")
        return True
    except Exception as e:
        print(f"ERRO: {e}")
        return False


def test_com_decimal_param():
    """Teste COM decimal=',' - deve funcionar."""
    print("\n" + "=" * 60)
    print("TESTE 2: Leitura COM decimal=',' (correcao proposta)")
    print("=" * 60)

    df = pd.read_csv(StringIO(SAMPLE_CSV), sep=";", decimal=",")

    print(f"\nTipos das colunas:")
    print(df.dtypes)

    print(f"\nValores de horascontratuais:")
    print(df['horascontratuais'].tolist())

    print(f"\nTentando converter para PyArrow...")
    try:
        table = pa.Table.from_pandas(df)
        print("SUCESSO - Converteu para PyArrow")
        return True
    except Exception as e:
        print(f"ERRO: {e}")
        return False


def test_com_dados_reais():
    """Testa com download real de um mes do CAGED."""
    print("\n" + "=" * 60)
    print("TESTE 3: Download real de um mes do CAGED")
    print("=" * 60)

    # Adiciona src ao path
    src_path = Path(__file__).parent.parent.parent / "src"
    sys.path.insert(0, str(src_path))

    from mte.caged.client import CAGEDClient

    client = CAGEDClient()

    try:
        print("\nConectando ao FTP...")
        client.connect()

        print("Baixando CAGEDMOV 2024-01 (teste)...")
        filepath = client._build_filepath("CAGEDMOV", 2024, 1)
        buffer = client.download_to_memory(filepath)

        # Testa SEM decimal
        print("\n--- Leitura SEM decimal=',' ---")
        buffer.seek(0)
        import tempfile
        import py7zr

        with tempfile.TemporaryDirectory() as tmpdir:
            with py7zr.SevenZipFile(buffer, mode='r') as archive:
                archive.extractall(path=tmpdir)

            csv_files = list(Path(tmpdir).glob("*.txt")) + list(Path(tmpdir).glob("*.csv"))
            csv_path = csv_files[0]

            # Sem decimal param
            df_sem = pd.read_csv(csv_path, encoding='latin-1', sep=";", nrows=100)
            print(f"Tipo horascontratuais: {df_sem['horascontratuais'].dtype}")
            print(f"Amostra: {df_sem['horascontratuais'].head(3).tolist()}")

            # Com decimal param
            df_com = pd.read_csv(csv_path, encoding='latin-1', sep=";", decimal=",", nrows=100)
            print(f"\n--- Leitura COM decimal=',' ---")
            print(f"Tipo horascontratuais: {df_com['horascontratuais'].dtype}")
            print(f"Amostra: {df_com['horascontratuais'].head(3).tolist()}")

            # Testa conversao para parquet
            print("\n--- Teste de conversao para PyArrow ---")
            try:
                pa.Table.from_pandas(df_com)
                print("SUCESSO com decimal=','")
            except Exception as e:
                print(f"ERRO com decimal=',': {e}")

        return True

    except Exception as e:
        print(f"Erro no teste real: {e}")
        return False
    finally:
        client.disconnect()


if __name__ == "__main__":
    print("Testando correcao do problema de decimal no CAGED\n")

    # Testes com dados simulados
    result1 = test_sem_decimal_param()
    result2 = test_com_decimal_param()

    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES SIMULADOS")
    print("=" * 60)
    print(f"Teste SEM decimal: {'FALHOU (esperado)' if not result1 else 'PASSOU (inesperado)'}")
    print(f"Teste COM decimal: {'PASSOU' if result2 else 'FALHOU'}")

    # Testa com dados reais
    print("\n" + "-" * 60)
    print("Testando com download real...")
    test_com_dados_reais()
