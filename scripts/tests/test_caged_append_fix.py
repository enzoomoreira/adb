"""
Testa a correcao do append para microdados do CAGED.

Valida que o parametro dedup=False funciona corretamente.
"""

import sys
from pathlib import Path
import tempfile
import shutil

import pandas as pd

# Adiciona src ao path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from data import DataManager
from mte.caged.client import CAGEDClient


def test_append_dedup_false():
    """Testa append com dedup=False usando dados simulados."""
    print("=" * 70)
    print("TESTE 1: append com dedup=False (dados simulados)")
    print("=" * 70)

    # Cria diretorio temporario
    with tempfile.TemporaryDirectory() as tmpdir:
        dm = DataManager(tmpdir)

        # Simula 3 meses de dados
        df1 = pd.DataFrame({
            'uf': [35, 33, 31],
            'salario': [1500, 2000, 1800],
            'ano_ref': [2024, 2024, 2024],
            'mes_ref': [1, 1, 1],
        })
        df2 = pd.DataFrame({
            'uf': [35, 33],
            'salario': [1600, 2100],
            'ano_ref': [2024, 2024],
            'mes_ref': [2, 2],
        })
        df3 = pd.DataFrame({
            'uf': [35, 33, 31, 41],
            'salario': [1700, 2200, 1900, 2500],
            'ano_ref': [2024, 2024, 2024, 2024],
            'mes_ref': [3, 3, 3, 3],
        })

        # Append com dedup=False
        print("\nAppend mes 1 (3 registros)...")
        dm.append(df1, 'test_caged', 'test', dedup=False)

        print("Append mes 2 (2 registros)...")
        dm.append(df2, 'test_caged', 'test', dedup=False)

        print("Append mes 3 (4 registros)...")
        dm.append(df3, 'test_caged', 'test', dedup=False)

        # Verifica resultado
        result = dm.read('test_caged', 'test')
        print(f"\nResultado: {len(result)} registros")

        # Verifica periodos
        periodos = result.groupby(['ano_ref', 'mes_ref']).size()
        print(f"Periodos: {len(periodos)}")
        for (ano, mes), count in periodos.items():
            print(f"  {ano}-{mes:02d}: {count} registros")

        esperado = 3 + 2 + 4
        if len(result) == esperado:
            print(f"\nSUCESSO! {esperado} registros preservados")
            return True
        else:
            print(f"\nFALHOU! Esperado {esperado}, obtido {len(result)}")
            return False


def test_append_dedup_true():
    """Testa que append com dedup=True ainda funciona para series temporais."""
    print("\n" + "=" * 70)
    print("TESTE 2: append com dedup=True (series temporais)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        dm = DataManager(tmpdir)

        # Simula serie temporal com indice de data
        df1 = pd.DataFrame({
            'value': [10.5, 10.75, 11.0],
        }, index=pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']))

        df2 = pd.DataFrame({
            'value': [11.25, 11.5],  # 01-03 e update, 01-04 e novo
        }, index=pd.to_datetime(['2024-01-03', '2024-01-04']))

        # Append com dedup=True (default)
        print("\nAppend serie 1 (3 datas)...")
        dm.append(df1, 'test_selic', 'test', dedup=True)

        print("Append serie 2 (2 datas, 1 update)...")
        dm.append(df2, 'test_selic', 'test', dedup=True)

        # Verifica
        result = dm.read('test_selic', 'test')
        print(f"\nResultado: {len(result)} registros")

        # Deve ter 4 registros (01-03 foi atualizado, nao duplicado)
        if len(result) == 4:
            # Verifica se 01-03 tem o valor atualizado
            val_0103 = result.loc['2024-01-03', 'value']
            if val_0103 == 11.25:
                print("SUCESSO! Dedup funcionou corretamente")
                return True
            else:
                print(f"FALHOU! Valor de 01-03 deveria ser 11.25, e {val_0103}")
                return False
        else:
            print(f"FALHOU! Esperado 4 registros, obtido {len(result)}")
            return False


def test_com_dados_reais():
    """Testa com download real de 2 meses do CAGED."""
    print("\n" + "=" * 70)
    print("TESTE 3: Com dados reais do CAGED (2 meses)")
    print("=" * 70)

    client = CAGEDClient()
    client.connect()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            dm = DataManager(tmpdir)

            # Baixa 2 meses
            for year, month in [(2024, 1), (2024, 2)]:
                print(f"\nBaixando {year}-{month:02d}...")
                df = client.get_data("CAGEDMOV", year, month, verbose=False)
                print(f"  {len(df):,} registros")

                # Limita para teste rapido
                df = df.head(1000)
                print(f"  Usando amostra de 1000 registros")

                dm.append(df, 'cagedmov', 'mte/caged', dedup=False)

            # Verifica
            result = dm.read('cagedmov', 'mte/caged')
            print(f"\nTotal salvo: {len(result):,} registros")

            periodos = result.groupby(['ano_ref', 'mes_ref']).size()
            print(f"Periodos: {len(periodos)}")

            if len(result) == 2000 and len(periodos) == 2:
                print("SUCESSO!")
                return True
            else:
                print("FALHOU!")
                return False

    finally:
        client.disconnect()


if __name__ == "__main__":
    results = {}

    results['dedup_false'] = test_append_dedup_false()
    results['dedup_true'] = test_append_dedup_true()
    results['dados_reais'] = test_com_dados_reais()

    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    for nome, passou in results.items():
        status = "PASSOU" if passou else "FALHOU"
        print(f"  {nome}: {status}")

    all_passed = all(results.values())
    print("\n" + "-" * 70)
    if all_passed:
        print("TODOS OS TESTES PASSARAM!")
        print("A correcao esta pronta. Pode rodar o collector completo.")
    else:
        print("ALGUNS TESTES FALHARAM!")
