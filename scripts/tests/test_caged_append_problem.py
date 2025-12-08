"""
Testa o problema de append do DataManager com microdados do CAGED.

Problema identificado:
- O append do DataManager remove duplicatas baseado no indice
- Microdados do CAGED tem indice numerico (0, 1, 2, ...)
- Quando concatena dois meses, indices se repetem
- Linha: combined = combined[~combined.index.duplicated(keep='last')]
- Resultado: apenas o ultimo mes e mantido!

Este script simula o problema e testa solucoes.
"""

import pandas as pd
import numpy as np
from io import BytesIO

# Simula dados de 3 meses do CAGED (simplificado)
def create_fake_month(year: int, month: int, n_records: int = 1000) -> pd.DataFrame:
    """Cria DataFrame fake simulando um mes do CAGED."""
    np.random.seed(year * 100 + month)  # Reproducibilidade
    return pd.DataFrame({
        'competênciamov': [int(f"{year}{month:02d}")] * n_records,
        'uf': np.random.choice([11, 12, 13, 21, 22, 31, 33, 35, 41, 43], n_records),
        'saldomovimentação': np.random.choice([-1, 1], n_records),
        'salário': np.random.uniform(1500, 5000, n_records).round(2),
        'idade': np.random.randint(18, 65, n_records),
        'ano_ref': year,
        'mes_ref': month,
    })


def test_problema_atual():
    """Demonstra o problema atual do append."""
    print("=" * 70)
    print("TESTE 1: Problema atual do append (simula DataManager.append)")
    print("=" * 70)

    # Simula 3 meses
    df1 = create_fake_month(2023, 1, n_records=100)
    df2 = create_fake_month(2023, 2, n_records=150)
    df3 = create_fake_month(2023, 3, n_records=200)

    print(f"\nMes 1: {len(df1)} registros, indices: {df1.index.min()}-{df1.index.max()}")
    print(f"Mes 2: {len(df2)} registros, indices: {df2.index.min()}-{df2.index.max()}")
    print(f"Mes 3: {len(df3)} registros, indices: {df3.index.min()}-{df3.index.max()}")

    # Simula append do DataManager (o problema)
    print("\n--- Simulando append do DataManager ---")

    # Primeiro append: df1 + df2
    combined = pd.concat([df1, df2])
    print(f"Apos concat df1+df2: {len(combined)} registros")
    combined = combined[~combined.index.duplicated(keep='last')]
    print(f"Apos remover duplicatas: {len(combined)} registros")

    # Segundo append: combined + df3
    combined = pd.concat([combined, df3])
    print(f"Apos concat +df3: {len(combined)} registros")
    combined = combined[~combined.index.duplicated(keep='last')]
    print(f"Apos remover duplicatas: {len(combined)} registros")

    # Verifica quantos meses restaram
    meses_restantes = combined[['ano_ref', 'mes_ref']].drop_duplicates()
    print(f"\nMeses no resultado final: {len(meses_restantes)}")
    print(meses_restantes.to_string(index=False))

    esperado = 100 + 150 + 200
    print(f"\nEsperado: {esperado} registros")
    print(f"Obtido: {len(combined)} registros")
    print(f"PROBLEMA: Perdemos {esperado - len(combined)} registros!")

    return len(combined) == esperado


def test_solucao_ignore_index():
    """Testa solucao: usar ignore_index=True no concat."""
    print("\n" + "=" * 70)
    print("TESTE 2: Solucao com ignore_index=True")
    print("=" * 70)

    df1 = create_fake_month(2023, 1, n_records=100)
    df2 = create_fake_month(2023, 2, n_records=150)
    df3 = create_fake_month(2023, 3, n_records=200)

    # Append com ignore_index=True (reseta indices)
    combined = pd.concat([df1, df2], ignore_index=True)
    print(f"Apos concat df1+df2 (ignore_index=True): {len(combined)} registros")
    print(f"  Indices: {combined.index.min()}-{combined.index.max()}")

    combined = pd.concat([combined, df3], ignore_index=True)
    print(f"Apos concat +df3 (ignore_index=True): {len(combined)} registros")
    print(f"  Indices: {combined.index.min()}-{combined.index.max()}")

    # Verifica
    meses = combined[['ano_ref', 'mes_ref']].drop_duplicates()
    print(f"\nMeses no resultado: {len(meses)}")

    esperado = 100 + 150 + 200
    print(f"Esperado: {esperado}, Obtido: {len(combined)}")

    if len(combined) == esperado:
        print("SUCESSO!")
        return True
    else:
        print("FALHOU!")
        return False


def test_solucao_sem_dedup():
    """Testa solucao: simplesmente nao remover duplicatas."""
    print("\n" + "=" * 70)
    print("TESTE 3: Solucao sem remocao de duplicatas")
    print("=" * 70)

    df1 = create_fake_month(2023, 1, n_records=100)
    df2 = create_fake_month(2023, 2, n_records=150)
    df3 = create_fake_month(2023, 3, n_records=200)

    # Append simples (sem dedup, sem ignore_index)
    combined = pd.concat([df1, df2])
    print(f"Apos concat df1+df2: {len(combined)} registros")

    combined = pd.concat([combined, df3])
    print(f"Apos concat +df3: {len(combined)} registros")

    # Nota: indices duplicados existem, mas dados estao corretos
    print(f"Indices duplicados? {combined.index.duplicated().any()}")

    meses = combined[['ano_ref', 'mes_ref']].drop_duplicates()
    print(f"Meses no resultado: {len(meses)}")

    esperado = 100 + 150 + 200
    print(f"Esperado: {esperado}, Obtido: {len(combined)}")

    if len(combined) == esperado:
        print("SUCESSO!")
        return True
    else:
        print("FALHOU!")
        return False


def test_solucao_append_raw():
    """Testa solucao: metodo append_raw sem dedup."""
    print("\n" + "=" * 70)
    print("TESTE 4: Simulando append_raw (proposta para DataManager)")
    print("=" * 70)

    def append_raw(existing_df, new_df):
        """Append para microdados - sem dedup, com ignore_index."""
        if existing_df.empty:
            return new_df.reset_index(drop=True)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
        return combined

    df1 = create_fake_month(2023, 1, n_records=100)
    df2 = create_fake_month(2023, 2, n_records=150)
    df3 = create_fake_month(2023, 3, n_records=200)

    # Primeiro "arquivo" vazio
    result = pd.DataFrame()

    result = append_raw(result, df1)
    print(f"Apos append df1: {len(result)} registros")

    result = append_raw(result, df2)
    print(f"Apos append df2: {len(result)} registros")

    result = append_raw(result, df3)
    print(f"Apos append df3: {len(result)} registros")

    # Testa salvar/carregar parquet
    print("\n--- Testando ciclo salvar/carregar Parquet ---")
    buf = BytesIO()
    result.to_parquet(buf, engine='pyarrow')
    buf.seek(0)
    loaded = pd.read_parquet(buf)

    print(f"Registros apos salvar/carregar: {len(loaded)}")
    print(f"Indices: {loaded.index.min()}-{loaded.index.max()}")

    meses = loaded[['ano_ref', 'mes_ref']].drop_duplicates()
    print(f"Meses preservados: {len(meses)}")

    esperado = 100 + 150 + 200
    if len(loaded) == esperado:
        print("SUCESSO!")
        return True
    else:
        print("FALHOU!")
        return False


def test_com_dados_reais_pequenos():
    """Testa com amostra real do CAGED (poucos registros)."""
    print("\n" + "=" * 70)
    print("TESTE 5: Com dados reais do CAGED (amostra pequena)")
    print("=" * 70)

    import sys
    from pathlib import Path

    src_path = Path(__file__).parent.parent.parent / "src"
    sys.path.insert(0, str(src_path))

    from mte.caged.client import CAGEDClient

    client = CAGEDClient()
    client.connect()

    try:
        # Baixa 2 meses com nrows limitado
        print("Baixando amostras de 2 meses...")

        # Mes 1
        filepath1 = client._build_filepath("CAGEDMOV", 2024, 1)
        buffer1 = client.download_to_memory(filepath1)

        import tempfile
        import py7zr

        with tempfile.TemporaryDirectory() as tmpdir:
            with py7zr.SevenZipFile(buffer1, mode='r') as archive:
                archive.extractall(path=tmpdir)
            csv_files = list(Path(tmpdir).glob("*.txt")) + list(Path(tmpdir).glob("*.csv"))
            df1 = pd.read_csv(csv_files[0], encoding='utf-8', sep=";", decimal=",", nrows=500)
            df1['ano_ref'] = 2024
            df1['mes_ref'] = 1

        # Mes 2
        filepath2 = client._build_filepath("CAGEDMOV", 2024, 2)
        buffer2 = client.download_to_memory(filepath2)

        with tempfile.TemporaryDirectory() as tmpdir:
            with py7zr.SevenZipFile(buffer2, mode='r') as archive:
                archive.extractall(path=tmpdir)
            csv_files = list(Path(tmpdir).glob("*.txt")) + list(Path(tmpdir).glob("*.csv"))
            df2 = pd.read_csv(csv_files[0], encoding='utf-8', sep=";", decimal=",", nrows=500)
            df2['ano_ref'] = 2024
            df2['mes_ref'] = 2

        print(f"Mes 1 (2024-01): {len(df1)} registros")
        print(f"Mes 2 (2024-02): {len(df2)} registros")

        # Testa append com ignore_index
        combined = pd.concat([df1, df2], ignore_index=True)
        print(f"\nCombinado (ignore_index=True): {len(combined)} registros")

        # Salva e recarrega
        buf = BytesIO()
        combined.to_parquet(buf, engine='pyarrow')
        buf.seek(0)
        loaded = pd.read_parquet(buf)

        print(f"Apos salvar/carregar Parquet: {len(loaded)} registros")

        # Segundo append simulando incremental
        combined2 = pd.concat([loaded, df1], ignore_index=True)  # Simula mais um mes
        print(f"Apos segundo append: {len(combined2)} registros")

        esperado = 500 + 500 + 500
        if len(combined2) == esperado:
            print("SUCESSO!")
            return True
        else:
            print(f"FALHOU! Esperado {esperado}, obtido {len(combined2)}")
            return False

    finally:
        client.disconnect()


if __name__ == "__main__":
    print("Testando problema e solucoes para append de microdados\n")

    results = {}

    # Teste do problema
    results['problema_atual'] = test_problema_atual()

    # Testes de solucoes
    results['ignore_index'] = test_solucao_ignore_index()
    results['sem_dedup'] = test_solucao_sem_dedup()
    results['append_raw'] = test_solucao_append_raw()

    # Teste com dados reais
    print("\n" + "-" * 70)
    print("Testando com dados reais do CAGED...")
    results['dados_reais'] = test_com_dados_reais_pequenos()

    # Resumo
    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    for nome, passou in results.items():
        status = "PASSOU" if passou else "FALHOU"
        print(f"  {nome}: {status}")

    print("\n" + "-" * 70)
    print("CONCLUSAO:")
    print("  - O problema atual e confirmado: append remove registros")
    print("  - Solucao recomendada: usar ignore_index=True no concat")
    print("  - Alternativa: criar metodo append_raw no DataManager")
