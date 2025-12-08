"""
Script para testar conexao FTP com o servidor do MTE.

Uso: uv run scripts/test_caged_connection.py
"""

from pathlib import Path
import sys

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mte.caged import CAGEDClient


def main():
    print("=" * 70)
    print("TESTE DE CONEXAO FTP - MTE/CAGED")
    print("=" * 70)
    print()

    client = CAGEDClient(timeout=60)

    # Teste 1: Conectar
    print("1. Testando conexao...")
    try:
        client.connect()
        print("   OK - Conectado ao servidor FTP")
        print(f"   Host: {client.FTP_HOST}")
    except Exception as e:
        print(f"   ERRO: {e}")
        return

    # Teste 2: Listar diretorios disponiveis
    print()
    print("2. Listando anos disponiveis...")
    try:
        years = client._ftp.nlst(client.BASE_PATH)
        print(f"   Encontrados: {len(years)} itens")
        for y in years[-5:]:  # Ultimos 5
            print(f"   - {y}")
    except Exception as e:
        print(f"   ERRO: {e}")

    # Teste 3: Listar meses de 2024
    print()
    print("3. Listando meses de 2024...")
    try:
        months = client._ftp.nlst(f"{client.BASE_PATH}/2024")
        print(f"   Encontrados: {len(months)} meses")
        for m in months[:5]:  # Primeiros 5
            print(f"   - {m}")
    except Exception as e:
        print(f"   ERRO: {e}")

    # Teste 4: Listar arquivos de um mes especifico
    print()
    print("4. Listando arquivos de 2024/202401...")
    try:
        files = client._ftp.nlst(f"{client.BASE_PATH}/2024/202401")
        print(f"   Encontrados: {len(files)} arquivos")
        for f in files:
            print(f"   - {f.split('/')[-1]}")
    except Exception as e:
        print(f"   ERRO: {e}")

    # Desconectar
    print()
    print("5. Desconectando...")
    client.disconnect()
    print("   OK - Desconectado")

    print()
    print("=" * 70)
    print("CONEXAO TESTADA COM SUCESSO!")
    print("=" * 70)


if __name__ == '__main__':
    main()
